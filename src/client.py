"""
Asynchronous User Notification System Client

This module provides a gRPC client for interacting with the notification service.
It allows sending messages and retrieving client statuses.
"""

import asyncio
import logging
from typing import Dict, Optional

import grpc
from grpc import aio

from notification_service_pb2 import (
    SendMessageRequest,
    GetClientStatusRequest,
    MessageType
)
from notification_service_pb2_grpc import NotificationServiceStub


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotificationClient:
    """
    Asynchronous gRPC client for the notification service.
    """
    
    def __init__(self, server_address: str = 'localhost:50051'):
        """
        Initialize the client with server address.
        
        Args:
            server_address: Address of the gRPC server
        """
        self.server_address = server_address
        self.channel: Optional[aio.Channel] = None
        self.stub: Optional[NotificationServiceStub] = None
        
    async def connect(self) -> None:
        """Establish connection to the gRPC server."""
        self.channel = aio.insecure_channel(self.server_address)
        self.stub = NotificationServiceStub(self.channel)
        logger.info(f"Connected to server at {self.server_address}")
    
    async def disconnect(self) -> None:
        """Close the connection to the gRPC server."""
        if self.channel:
            await self.channel.close()
            logger.info("Disconnected from server")
    
    async def send_hello(self, client_id: str) -> bool:
        """
        Send a HELLO message for a client.
        
        Args:
            client_id: ID of the client sending the message
            
        Returns:
            True if successful, False otherwise
        """
        return await self._send_message(client_id, MessageType.HELLO)
    
    async def send_goodbye(self, client_id: str) -> bool:
        """
        Send a GOODBYE message for a client.
        
        Args:
            client_id: ID of the client sending the message
            
        Returns:
            True if successful, False otherwise
        """
        return await self._send_message(client_id, MessageType.GOODBYE)
    
    async def _send_message(self, client_id: str, message_type: MessageType) -> bool:
        """
        Send a message to the server.
        
        Args:
            client_id: ID of the client
            message_type: Type of message to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        try:
            request = SendMessageRequest(
                client_id=client_id,
                message_type=message_type
            )
            
            response = await self.stub.SendMessage(request)
            
            if response.success:
                # Convert enum to string safely
                message_type_name = MessageType.Name(message_type) if hasattr(MessageType, 'Name') else str(message_type)
                logger.info(f"Successfully sent {message_type_name} for client {client_id}")
                return True
            else:
                logger.warning(f"Failed to send message: {response.message}")
                return False
                
        except grpc.RpcError as e:
            logger.error(f"gRPC error sending message: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    async def get_client_status(self, client_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get client connection statuses.
        
        Args:
            client_id: Optional specific client ID to query
            
        Returns:
            Dictionary of client statuses
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        try:
            request = GetClientStatusRequest()
            if client_id:
                request.client_id = client_id
            
            response = await self.stub.GetClientStatus(request)
            logger.info(f"Retrieved status for {len(response.client_statuses)} clients")
            return dict(response.client_statuses)
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error getting client status: {e.code()} - {e.details()}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting client status: {e}")
            return {}


async def main():
    """Example usage of the notification client."""
    client = NotificationClient()
    
    try:
        await client.connect()
        
        # Example: Send messages for different clients
        await client.send_hello("client_1")
        await client.send_hello("client_2")
        await client.send_goodbye("client_1")
        
        # Get all client statuses
        statuses = await client.get_client_status()
        print("All client statuses:", statuses)
        
        # Get specific client status
        client_1_status = await client.get_client_status("client_1")
        print("Client 1 status:", client_1_status)
        
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())