"""
Asynchronous User Notification System Server

This module implements a gRPC server that handles user connection notifications
asynchronously. It manages client connection states and provides APIs to send
messages and retrieve client statuses.
"""

import asyncio
import logging
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

import grpc
from grpc import aio

from notification_service_pb2 import (
    SendMessageRequest,
    SendMessageResponse,
    GetClientStatusRequest,
    GetClientStatusResponse,
    MessageType
)
from notification_service_pb2_grpc import NotificationServiceServicer, add_NotificationServiceServicer_to_server


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotificationServiceImpl(NotificationServiceServicer):
    """
    Implementation of the NotificationService gRPC servicer.
    
    This class handles user connection management with in-memory storage
    and provides asynchronous message processing capabilities.
    """
    
    def __init__(self):
        """Initialize the service with empty client status storage."""
        self._client_statuses: Dict[str, str] = {}
        self._lock = threading.RLock()  # Thread-safe access to client statuses
        logger.info("NotificationService initialized")
    
    async def SendMessage(self, request: SendMessageRequest, context: grpc.aio.ServicerContext) -> SendMessageResponse:
        """
        Handle incoming messages from clients.
        
        Args:
            request: SendMessageRequest containing client_id and message_type
            context: gRPC context for the request
            
        Returns:
            SendMessageResponse indicating success or failure
            
        Raises:
            grpc.RpcError: For invalid message types or missing client_id
        """
        logger.info(f"Received message from client: {request.client_id}, type: {request.message_type}")
        
        # Validate client_id
        if not request.client_id or not request.client_id.strip():
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Client ID cannot be empty"
            )
        
        client_id = request.client_id.strip()
        
        try:
            # Process message asynchronously
            await self._process_message_async(client_id, request.message_type)
            
            response = SendMessageResponse(
                success=True,
                message=f"Message processed successfully for client {client_id}"
            )
            logger.info(f"Successfully processed message for client: {client_id}")
            return response
            
        except ValueError as e:
            logger.warning(f"Invalid message type for client {client_id}: {e}")
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                str(e)
            )
        except Exception as e:
            logger.error(f"Error processing message for client {client_id}: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Internal server error"
            )
    
    async def GetClientStatus(self, request: GetClientStatusRequest, context: grpc.aio.ServicerContext) -> GetClientStatusResponse:
        """
        Retrieve client connection statuses.
        
        Args:
            request: GetClientStatusRequest optionally containing specific client_id
            context: gRPC context for the request
            
        Returns:
            GetClientStatusResponse containing client statuses
        """
        logger.info(f"Client status requested for: {request.client_id if request.client_id else 'all clients'}")
        
        try:
            with self._lock:
                if request.client_id and request.client_id.strip():
                    # Return specific client status
                    client_id = request.client_id.strip()
                    if client_id in self._client_statuses:
                        client_statuses = {client_id: self._client_statuses[client_id]}
                    else:
                        client_statuses = {}
                else:
                    # Return all client statuses
                    client_statuses = dict(self._client_statuses)
            
            response = GetClientStatusResponse(client_statuses=client_statuses)
            logger.info(f"Returned status for {len(client_statuses)} clients")
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving client status: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Internal server error"
            )
    
    async def _process_message_async(self, client_id: str, message_type: MessageType) -> None:
        """
        Process incoming messages asynchronously.
        
        Args:
            client_id: The ID of the client sending the message
            message_type: The type of message (HELLO or GOODBYE)
            
        Raises:
            ValueError: For invalid message types
        """
        # Simulate async processing delay
        await asyncio.sleep(0.01)
        
        with self._lock:
            if message_type == MessageType.HELLO:
                self._client_statuses[client_id] = "connected"
                logger.info(f"Client {client_id} marked as connected")
            elif message_type == MessageType.GOODBYE:
                self._client_statuses[client_id] = "disconnected"
                logger.info(f"Client {client_id} marked as disconnected")
            else:
                raise ValueError(f"Invalid message type: {message_type}")
    
    def get_client_status_sync(self, client_id: Optional[str] = None) -> Dict[str, str]:
        """
        Synchronous method to get client statuses (for testing purposes).
        
        Args:
            client_id: Optional specific client ID to query
            
        Returns:
            Dictionary of client statuses
        """
        with self._lock:
            if client_id:
                return {client_id: self._client_statuses.get(client_id, "unknown")}
            return dict(self._client_statuses)


async def serve(port: int = 50051) -> None:
    """
    Start the gRPC server.
    
    Args:
        port: Port number to bind the server to (default: 50051)
    """
    server = aio.server(ThreadPoolExecutor(max_workers=10))
    
    # Add our service implementation
    service_impl = NotificationServiceImpl()
    add_NotificationServiceServicer_to_server(service_impl, server)
    
    # Bind to port
    listen_addr = f'[::]:{port}'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting server on {listen_addr}")
    await server.start()
    
    logger.info("Server started successfully. Press Ctrl+C to stop.")
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        await server.stop(5)


if __name__ == '__main__':
    asyncio.run(serve())