    async def _authentication_node(self, state: AgentState) -> AgentState:
        """Nodo de autenticación con persistencia por teléfono"""
        session_id = state["session_id"]

        # Verificar si ya está autenticado en la sesión actual (memoria en RAM)
        if session_manager.is_authenticated(session_id):
            user = session_manager.get_user(session_id)
            state["user_info"] = {
                "id": user.id,
                "nombre": user.nombre,
                "legajo": user.legajo,
                "tipo": user.tipo
            }
            # Usuario autenticado - ir directo al supervisor
            state["next"] = "supervisor"
            return state

        # NUEVO: Buscar si este teléfono tiene usuario asociado en BD
        from app.database import phone_repository, user_repository
        
        logger.info(f"🔍 Buscando asociación persistente para teléfono {session_id}")
        usuario_id = await phone_repository.get_user_by_phone(session_id)
        
        if usuario_id:
            # Auto-autenticar usando el usuario_id almacenado
            logger.info(f"✅ Asociación encontrada! Auto-autenticando usuario {usuario_id}")
            user = await user_repository.get_user_by_id(usuario_id)
            
            if user:
                session_manager.authenticate_user(session_id, user)
                state["user_info"] = {
                    "id": user.id,
                    "nombre": user.nombre,
                    "legajo": user.legajo,
                    "tipo": user.tipo
                }
                
                response = f"¡Hola de nuevo, {user.nombre}! 👋\n\n¿En qué te puedo ayudar hoy?"
                state["messages"].append(AIMessage(content=response))
                state["next"] = "END"
                return state
            else:
                logger.error(f"⚠️ Usuario {usuario_id} no encontrado en BD. Eliminando asociación inválida.")
                await phone_repository.delete_phone_mapping(session_id)

        # Proceso de autenticación por DNI
        last_message = state["messages"][-1].content if state["messages"] else ""

        # Detectar comando de logout/olvidar
        if any(word in last_message.lower() for word in ["olvidar", "logout", "cerrar sesion", "cerrar sesión"]):
            await phone_repository.delete_phone_mapping(session_id)
            logger.info(f"🛡️ Usuario solicitó olvidar su información")
            response = "He olvidado tu información. 🛡️\n\nLa próxima vez te pediré tu DNI nuevamente.\n\n¿Hay algo más en lo que te pueda ayudar?"
            state["messages"].append(AIMessage(content=response))
            state["next"] = "END"
            return state

        # Buscar DNI en el mensaje
        import re
        dni_pattern = r'\b\d{8}\b'
        dni_match = re.search(dni_pattern, last_message)

        if dni_match:
            dni = dni_match.group()
            # Autenticar usuario
            user = await self._authenticate_user(dni)

            if user:
                session_manager.authenticate_user(session_id, user)
                state["user_info"] = {
                    "id": user.id,
                    "nombre": user.nombre,
                    "legajo": user.legajo,
                    "tipo": user.tipo
                }

                # NUEVO: Guardar asociación teléfono → usuario en BD
                logger.info(f"💾 Guardando asociación persistente: {session_id} → {user.id}")
                await phone_repository.save_phone_user_mapping(session_id, user.id)

                response = f"¡Perfecto, {user.nombre}! Ya te reconocí.\n\n¿En qué te puedo ayudar hoy?"
                state["messages"].append(AIMessage(content=response))
                # Terminar aquí - NO ir al supervisor automáticamente
                state["next"] = "END"
            else:
                response = "Lo siento, no reconozco ese DNI en nuestra base de datos.\n\nPor favor verificá el número."
                state["messages"].append(AIMessage(content=response))
                state["next"] = "END"
        else:
            response = "¡Hola! Para ayudarte necesito que me pases tu DNI (solo números)."
            state["messages"].append(AIMessage(content=response))
            state["next"] = "END"

        return state

