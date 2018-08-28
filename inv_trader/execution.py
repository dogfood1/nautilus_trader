#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------------------------
# <copyright file="execution.py" company="Invariance Pte">
#  Copyright (C) 2018 Invariance Pte. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE.md file.
#  http://www.invariance.com
# </copyright>
# -------------------------------------------------------------------------------------------------

import abc
import uuid
import zmq

from datetime import datetime
from decimal import Decimal
from typing import Dict, Callable
from uuid import UUID

from inv_trader.core.checks import typechecking
from inv_trader.model.order import Order
from inv_trader.model.commands import SubmitOrder, CancelOrder, ModifyOrder
from inv_trader.model.events import Event, OrderEvent, AccountEvent, OrderCancelReject
from inv_trader.messaging import RequestWorker, SubscriberWorker
from inv_trader.strategy import TradeStrategy
from inv_trader.serialization import MsgPackCommandSerializer
from inv_trader.serialization import MsgPackEventSerializer

# Constants
UTF8 = 'utf-8'
OrderId = str


class ExecutionClient:
    """
    The abstract base class for all execution clients.
    """

    __metaclass__ = abc.ABCMeta

    @typechecking
    def __init__(self):
        """
        Initializes a new instance of the ExecutionClient class.
        """
        self._event_serializer = MsgPackEventSerializer
        self._command_serializer = MsgPackCommandSerializer
        self._registered_strategies = {}  # type: Dict[UUID, Callable]
        self._order_index = {}            # type: Dict[OrderId, UUID]

        self._log("Initialized.")

    @typechecking
    def register_strategy(self, strategy: TradeStrategy):
        """
        Register the given strategy with the execution client.
        """
        if strategy.id in self._registered_strategies.keys():
            raise ValueError("The strategy must have a unique name and label.")

        self._registered_strategies[strategy.id] = strategy._update_events
        strategy._register_execution_client(self)

    @abc.abstractmethod
    def connect(self):
        """
        Connect to the execution service.
        """
        # Raise exception if not overridden in implementation.
        raise NotImplementedError("Method must be implemented in the execution client.")

    @abc.abstractmethod
    def disconnect(self):
        """
        Disconnect from the execution service.
        """
        # Raise exception if not overridden in implementation.
        raise NotImplementedError("Method must be implemented in the execution client.")

    @abc.abstractmethod
    def submit_order(
            self,
            order: Order,
            strategy_id: UUID):
        """
        Send a submit order request to the execution service.
        """
        # Raise exception if not overridden in implementation.
        raise NotImplementedError("Method must be implemented in the execution client.")

    @abc.abstractmethod
    def cancel_order(
            self, order: Order,
            cancel_reason: str):
        """
        Send a cancel order request to the execution service.
        """
        # Raise exception if not overridden in implementation.
        raise NotImplementedError("Method must be implemented in the execution client.")

    @abc.abstractmethod
    def modify_order(
            self,
            order: Order,
            new_price: Decimal):
        """
        Send a modify order request to the execution service.
        """
        # Raise exception if not overridden in implementation.
        raise NotImplementedError("Method must be implemented in the execution client.")

    @typechecking
    def _register_order(
            self,
            order: Order,
            strategy_id: UUID):
        """
        Register the given order with the execution client.

        :param order: The order to register.
        :param strategy_id: The strategy id to register with the order.
        """
        if order.id in self._order_index.keys():
            raise ValueError(f"The order does not have a unique id.")

        self._order_index[order.id] = strategy_id

    @typechecking
    def _on_event(self, event: Event):
        """
        Handle events received from the execution service.
        """
        # Order event
        self._log(f"Received {event}.")
        if isinstance(event, OrderEvent):
            order_id = event.order_id
            if order_id not in self._order_index.keys():
                self._log(
                    f"[Warning]: The given event order id {order_id} "
                    f"was not contained in the order index.")
                return

            strategy_id = self._order_index[order_id]
            self._registered_strategies[strategy_id](event)

        if isinstance(event, OrderCancelReject):
            self._log(f"[Warning]: {event}.")

        if isinstance(event, AccountEvent):
            for strategy_id in self._registered_strategies.keys():
                self._registered_strategies[strategy_id](event)

    @staticmethod
    @typechecking
    def _log(message: str):
        """
        Log the given message (if no logger then prints).

        :param message: The message to log.
        """
        print(f"ExecClient: {message}")


class LiveExecClient(ExecutionClient):
    """
    Provides a live execution client for trading strategies utilizing an AMQP
    (Advanced Message Queue Protocol) 0-9-1 message broker.
    """

    @typechecking
    def __init__(
            self,
            host_address: str='localhost',
            commands_port: int=5555,
            events_port: int=5556):
        """
        Initializes a new instance of the LiveExecClient class.
        The host and port parameters are for the order event subscription
        channel.

        :param host_address: The execution service host IP address (default=127.0.0.1).
        :param commands_port: The execution service commands port.
        :param events_port: The execution service events port.
        """
        super().__init__()
        self._context = zmq.Context()
        self._order_commands_worker = RequestWorker(
            'CommandSender',
            self._context,
            host_address,
            commands_port,
            self._command_ack_handler)

        self._order_events_worker = SubscriberWorker(
            "EventSubscriber",
            self._context,
            host_address,
            events_port,
            "nautilus_execution_events",
            self._event_handler)

        self._log(f"ZMQ v{zmq.pyzmq_version()}")

    def connect(self):
        """
        Connect to the execution service.
        """
        self._order_events_worker.start()
        self._order_commands_worker.start()

    def disconnect(self):
        """
        Disconnect from the execution service.
        """
        self._order_commands_worker.stop()
        self._order_events_worker.stop()

    @typechecking
    def submit_order(
            self,
            order: Order,
            strategy_id: UUID):
        """
        Send a submit order request to the execution service.

        :param: order: The order to submit.
        :param: strategy_id: The strategy identifier to register the order with.
        """
        super()._register_order(order, strategy_id)

        command = SubmitOrder(
            order,
            uuid.uuid4(),
            datetime.utcnow())
        message = MsgPackCommandSerializer.serialize(command)

        self._order_commands_worker.send(message)
        self._log(f"Sent {command}.")

    @typechecking
    def cancel_order(
            self,
            order: Order,
            cancel_reason: str):
        """
        Send a cancel order request to the execution service.

        :param: order: The order identifier to cancel.
        :param: cancel_reason: The reason for cancellation (will be logged).
        """
        command = CancelOrder(
            order,
            cancel_reason,
            uuid.uuid4(),
            datetime.utcnow())
        message = MsgPackCommandSerializer.serialize(command)

        self._order_commands_worker.send(message)
        self._log(f"Sent {command}.")

    @typechecking
    def modify_order(
            self,
            order: Order,
            new_price: Decimal):
        """
        Send a modify order request to the execution service.

        :param: order: The order identifier to modify.
        :param: new_price: The new modified price for the order.
        """
        command = ModifyOrder(
            order,
            new_price,
            uuid.uuid4(),
            datetime.utcnow())
        message = MsgPackCommandSerializer.serialize(command)

        self._order_commands_worker.send(message)
        self._log(f"Sent {command}.")

    @typechecking
    def _event_handler(self, body: bytes):
        """"
        Handle the event message by parsing to an Event and sending
        to the registered strategy.

        :param body: The order event message body.
        """
        event = self._event_serializer.deserialize(body)

        # If no registered strategies then print message to console.
        if len(self._registered_strategies) == 0:
            self._log(f"Received event from queue: {event}")

        self._on_event(event)

    @typechecking
    def _command_ack_handler(self, body: bytes):
        """"
        Handle the command acknowledgement message.

        :param body: The order command acknowledgement message body.
        """
        command = MsgPackCommandSerializer.deserialize(body)
        self._log(f"Received order command ack {command}.")
