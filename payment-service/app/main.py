import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.logger import logger
from app.schemas import PaymentInitRequest, PaymentResultResponse, RefundRequest, RefundResponse
from app.ticket_client import confirm_ticket, cancel_ticket, notify
from app.logging_service import log_action
from pydantic import BaseModel

class BulkPaymentRequest(BaseModel):
    ticket_ids: list[int]
    total_amount: float
    email: str

app = FastAPI(
    title="Payment Service",
    docs_url="/docs"
)

# CORS для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище платежей
payments = {}


@app.on_event("startup")
def startup():
    logger.info("Payment Service started")


@app.post("/api/payment/payment/init", response_model=PaymentResultResponse)
def init_payment_api(request: PaymentInitRequest):
    """Обработать платёж за билет - УЧЕБНАЯ ИМИТАЦИЯ (2/3 успех)"""
    logger.info(f"Payment initiated for ticket {request.ticket_id}, amount {request.amount}, email {request.email}")

    # Валидация суммы
    if request.amount <= 0:
        logger.warning(f"Invalid amount: {request.amount}")
        cancel_ticket(request.ticket_id)
        return PaymentResultResponse(
            ticket_id=request.ticket_id,
            status="FAILED",
            message="Некорректная сумма платежа"
        )

    # УЧЕБНАЯ ИМИТАЦИЯ: случайный результат (50% успех, 50% ошибка)
    success = random.choice([True, False])
    
    try:
        if success:
            # Подтвердить билет
            confirm_ticket(request.ticket_id)
            
            # Отправить уведомление
            notify(request.ticket_id, "purchase", request.email)
            
            logger.info(f"Payment successful for ticket {request.ticket_id}")
            
            # Логируем действие пользователя
            log_action(
                action="PAYMENT_SUCCESS",
                user_id=request.email or "anonymous",
                details={
                    "ticket_id": request.ticket_id,
                    "amount": request.amount,
                    "email": request.email
                }
            )
            
            return PaymentResultResponse(
                ticket_id=request.ticket_id,
                status="SUCCESS",
                message="Платёж успешно обработан"
            )
        else:
            # Отменить билет
            cancel_ticket(request.ticket_id)
            
            # Отправить уведомление
            notify(request.ticket_id, "cancellation", request.email)
            
            logger.warning(f"Payment failed for ticket {request.ticket_id}")
            
            # Логируем действие пользователя
            log_action(
                action="PAYMENT_FAILED",
                user_id=request.email or "anonymous",
                details={
                    "ticket_id": request.ticket_id,
                    "amount": request.amount,
                    "email": request.email
                }
            )
            
            return PaymentResultResponse(
                ticket_id=request.ticket_id,
                status="FAILED",
                message="Ошибка обработки платежа. Попробуйте ещё раз."
            )
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        cancel_ticket(request.ticket_id)
        return PaymentResultResponse(
            ticket_id=request.ticket_id,
            status="FAILED",
            message="Внутренняя ошибка сервера"
        )


@app.post("/payment/init", response_model=PaymentResultResponse)
def init_payment(request: PaymentInitRequest):
    """Обработать платёж за билет - УЧЕБНАЯ ИМИТАЦИЯ (2/3 успех)"""
    logger.info(f"Payment initiated for ticket {request.ticket_id}, amount {request.amount}, email {request.email}")

    # Валидация суммы
    if request.amount <= 0:
        logger.warning(f"Invalid amount: {request.amount}")
        cancel_ticket(request.ticket_id)
        return PaymentResultResponse(
            ticket_id=request.ticket_id,
            status="FAILED",
            message="Некорректная сумма платежа"
        )

    # УЧЕБНАЯ ИМИТАЦИЯ: случайный результат (50% успех, 50% ошибка)
    success = random.choice([True, False])
    
    try:
        if success:
            # Подтвердить билет
            confirm_ticket(request.ticket_id)
            
            # Отправить уведомление
            notify(request.ticket_id, "purchase", request.email)
            
            logger.info(f"Payment successful for ticket {request.ticket_id}")
            
            # Логируем действие пользователя
            log_action(
                action="PAYMENT_SUCCESS",
                user_id=request.email or "anonymous",
                details={
                    "ticket_id": request.ticket_id,
                    "amount": request.amount,
                    "email": request.email
                }
            )
            
            return PaymentResultResponse(
                ticket_id=request.ticket_id,
                status="SUCCESS",
                message="Платёж успешно обработан"
            )
        else:
            # Отменить билет
            cancel_ticket(request.ticket_id)
            
            # Отправить уведомление
            notify(request.ticket_id, "cancellation", request.email)
            
            logger.warning(f"Payment failed for ticket {request.ticket_id}")
            
            # Логируем действие пользователя
            log_action(
                action="PAYMENT_FAILED",
                user_id=request.email or "anonymous",
                details={
                    "ticket_id": request.ticket_id,
                    "amount": request.amount,
                    "email": request.email
                }
            )
            
            return PaymentResultResponse(
                ticket_id=request.ticket_id,
                status="FAILED",
                message="Ошибка обработки платежа. Попробуйте ещё раз."
            )
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        cancel_ticket(request.ticket_id)
        return PaymentResultResponse(
            ticket_id=request.ticket_id,
            status="FAILED",
            message="Внутренняя ошибка сервера"
        )


@app.post("/payment/refund", response_model=RefundResponse)
def refund_payment(request: RefundRequest):
    """Вернуть деньги за билет"""
    logger.info(f"Refund requested for ticket {request.ticket_id}, reason: {request.reason}")
    
    try:
        # Отменяем билет напрямую через ticket-service
        cancel_ticket(request.ticket_id)
        
        logger.info(f"Refund successful for ticket {request.ticket_id}")
        
        # Логируем действие пользователя
        log_action(
            action="PAYMENT_REFUND",
            user_id="anonymous",  # TODO: получить email из запроса
            details={
                "ticket_id": request.ticket_id,
                "reason": request.reason
            }
        )
        
        return RefundResponse(
            ticket_id=request.ticket_id,
            status="SUCCESS",
            refunded_amount=0,  # Мы не знаем сумму, но возвращаем успешно
            message=f"✅ Возврат билета {request.ticket_id} успешен!"
        )
    except Exception as e:
        logger.error(f"Refund error for ticket {request.ticket_id}: {e}")
        return RefundResponse(
            ticket_id=request.ticket_id,
            status="FAILED",
            refunded_amount=0,
            message=f"❌ Ошибка при возврате билета: {str(e)}"
        )


@app.post("/api/payment/bulk-payment", response_model=PaymentResultResponse)
def bulk_payment(request: BulkPaymentRequest):
    """Групповая оплата билетов - один шанс для всех билетов"""
    logger.info(f"Bulk payment initiated for tickets {request.ticket_ids}, total amount {request.total_amount}, email {request.email}")

    # Валидация суммы
    if request.total_amount <= 0:
        logger.warning(f"Invalid total amount: {request.total_amount}")
        # Отменяем все билеты
        for ticket_id in request.ticket_ids:
            try:
                cancel_ticket(ticket_id)
            except:
                pass
        return PaymentResultResponse(
            ticket_id=0,  # Групповая операция
            status="FAILED",
            message="Некорректная сумма платежа"
        )

    # УЧЕБНАЯ ИМИТАЦИЯ: случайный результат (50% успех, 50% ошибка) для всей группы
    success = random.choice([True, False])
    
    try:
        if success:
            # Подтверждаем все билеты
            confirmed_tickets = []
            for ticket_id in request.ticket_ids:
                try:
                    confirm_ticket(ticket_id)
                    confirmed_tickets.append(ticket_id)
                except Exception as e:
                    logger.error(f"Error confirming ticket {ticket_id}: {e}")
            
            # Отправляем уведомления для всех билетов
            for ticket_id in request.ticket_ids:
                try:
                    notify(ticket_id, "purchase", request.email)
                except:
                    pass
            
            logger.info(f"Bulk payment successful for tickets {request.ticket_ids}")
            
            # Логируем действие пользователя
            log_action(
                action="BULK_PAYMENT_SUCCESS",
                user_id=request.email or "anonymous",
                details={
                    "ticket_ids": request.ticket_ids,
                    "total_amount": request.total_amount,
                    "email": request.email,
                    "confirmed_tickets": confirmed_tickets
                }
            )
            
            return PaymentResultResponse(
                ticket_id=0,  # Групповая операция
                status="SUCCESS",
                message=f"💰 Оплата всех билетов успешна! Оплачено билетов: {len(confirmed_tickets)}"
            )
        else:
            # Отменяем все билеты
            cancelled_tickets = []
            for ticket_id in request.ticket_ids:
                try:
                    cancel_ticket(ticket_id)
                    cancelled_tickets.append(ticket_id)
                except Exception as e:
                    logger.error(f"Error cancelling ticket {ticket_id}: {e}")
            
            logger.warning(f"Bulk payment failed for tickets {request.ticket_ids}")
            
            # Логируем действие пользователя
            log_action(
                action="BULK_PAYMENT_FAILED",
                user_id=request.email or "anonymous",
                details={
                    "ticket_ids": request.ticket_ids,
                    "total_amount": request.total_amount,
                    "email": request.email,
                    "cancelled_tickets": cancelled_tickets
                }
            )
            
            return PaymentResultResponse(
                ticket_id=0,  # Групповая операция
                status="FAILED",
                message=f"💸 Оплата не удалась. Все билеты ({len(cancelled_tickets)}) отменены."
            )
    except Exception as e:
        logger.error(f"Bulk payment processing error: {e}")
        # Отменяем все билеты при ошибке
        for ticket_id in request.ticket_ids:
            try:
                cancel_ticket(ticket_id)
            except:
                pass
        return PaymentResultResponse(
            ticket_id=0,  # Групповая операция
            status="FAILED",
            message="Внутренняя ошибка сервера"
        )