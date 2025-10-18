    async def process_message_stream(self, message: str, session_id: str) -> str:
        """
        Procesa un mensaje a través del workflow LangGraph.
        
        NOTA: Usa el mismo flujo que process_message pero con logging mejorado.
        El streaming interno del LLM ya está habilitado en __init__.

        Args:
            message: Mensaje del usuario (puede ser múltiples mensajes unidos)
            session_id: ID de sesión único

        Returns:
            Respuesta completa del sistema
        """
        try:
            logger.info(f"🚀 Procesando mensaje con streaming para sesión {session_id}")
            
            # Estado inicial
            initial_state: AgentState = {
                "messages": [HumanMessage(content=message)],
                "next": "authentication",
                "user_info": {},
                "session_id": session_id,
                "agent_scratchpad": {},
                "escalation_requested": False,
                "confidence_score": 1.0
            }

            # Configuración con LangSmith tags
            config = {
                "configurable": {"thread_id": session_id},
                "recursion_limit": 10,
                "tags": [
                    f"session:{session_id}",
                    "streaming:enabled",
                    "source:whatsapp"
                ],
                "metadata": {
                    "session_id": session_id,
                    "message_preview": message[:100],
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Ejecutar workflow normalmente (el streaming del LLM está habilitado internamente)
            result = await self.app.ainvoke(initial_state, config)

            # Extraer la respuesta del agente
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            
            if ai_messages:
                # Buscar la respuesta más larga (la del agente, no solo metadatos)
                full_response = ""
                for msg in reversed(ai_messages):
                    if msg.content and len(msg.content) > 20:
                        full_response = msg.content
                        logger.info(f"✅ Respuesta encontrada: {len(full_response)} caracteres")
                        break
                
                # Si no encontramos nada largo, usar el último
                if not full_response and ai_messages:
                    full_response = ai_messages[-1].content
                    logger.warning(f"⚠️ Usando último mensaje aunque es corto: '{full_response}'")
                
                if full_response:
                    return full_response
                else:
                    logger.error("❌ No se encontró respuesta válida en ai_messages")
                    return "Lo siento, hubo un problema procesando tu mensaje."
            else:
                logger.error("❌ No hay mensajes de IA en el resultado")
                return "Lo siento, hubo un problema procesando tu mensaje."

        except Exception as e:
            logger.error(f"❌ Error en SupervisorAgent.process_message_stream: {e}", exc_info=True)
            return "Hubo un error técnico. Por favor intentá de nuevo."
