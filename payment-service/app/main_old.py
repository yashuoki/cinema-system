import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.logger import logger
from app.schemas import PaymentInitRequest, PaymentResultResponse, RefundRequest, RefundResponse
from app.ticket_client import confirm_ticket, cancel_ticket, notify

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

    # ВСЕГДА УСПЕШНАЯ ОПЛАТА - для стабильной работы
    success = True
    logger.info(f"Payment random result for ticket {request.ticket_id}: {success}")
    
    try:
        if success:
            # Подтвердить билет
            confirm_ticket(request.ticket_id)
            
            # Отправить уведомление
            notify(request.ticket_id, "purchase", request.email)
            
            logger.info(f"Payment successful for ticket {request.ticket_id}")
            
            # Обновляем метрики в session-service
            try:
                import httpx
                # Увеличиваем счетчик успешных оплат
                response1 = httpx.post(
                    "http://session-service:8000/api/monitoring/increment",
                    params={"metric_name": "payment_success"}
                )
                # Увеличиваем счетчик проданных билетов
                response2 = httpx.post(
                    "http://session-service:8000/api/monitoring/increment",
                    params={"metric_name": "sold"}
                )
                if response1.status_code == 200 and response2.status_code == 200:
                    logger.info("Metrics 'payment_success' and 'sold' updated successfully")
            except Exception as e:
                logger.warning(f"Failed to update metrics: {e}")
            
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

    # ВСЕГДА УСПЕШНАЯ ОПЛАТА - для стабильной работы
    success = True
    logger.info(f"Payment random result for ticket {request.ticket_id}: {success}")
    
    try:
        if success:
            # Подтвердить билет
            confirm_ticket(request.ticket_id)
            
            # Отправить уведомление
            notify(request.ticket_id, "purchase", request.email)
            
            logger.info(f"Payment successful for ticket {request.ticket_id}")
            
            # Обновляем метрики в session-service
            try:
                import httpx
                # Увеличиваем счетчик успешных оплат
                response1 = httpx.post(
                    "http://session-service:8000/api/monitoring/increment",
                    params={"metric_name": "payment_success"}
                )
                # Увеличиваем счетчик проданных билетов
                response2 = httpx.post(
                    "http://session-service:8000/api/monitoring/increment",
                    params={"metric_name": "sold"}
                )
                if response1.status_code == 200 and response2.status_code == 200:
                    logger.info("Metrics 'payment_success' and 'sold' updated successfully")
            except Exception as e:
                logger.warning(f"Failed to update metrics: {e}")
            
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
def init_payment_alt(request: PaymentInitRequest):
    """Обработать платёж за билет - УЧЕБНАЯ ИМИТАЦИЯ (50% успех, 50% ошибка)"""
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
    
    # ВСЕГДА УСПЕШНАЯ ОПЛАТА - для стабильной работы
    success = True
    logger.info(f"Payment random result for ticket {request.ticket_id}: {success}")
    
    try:
        if success:
            # Подтвердить билет
            confirm_ticket(request.ticket_id)
            
            # Отправить уведомление
            notify(request.ticket_id, "purchase", request.email)
            
            logger.info(f"Payment successful for ticket {request.ticket_id}")
            
            # Обновляем метрики в session-service
            try:
                import httpx
                # Увеличиваем счетчик успешных оплат
                response1 = httpx.post(
                    "http://session-service:8000/api/monitoring/increment",
                    params={"metric_name": "payment_success"}
                )
                # Увеличиваем счетчик проданных билетов
                response2 = httpx.post(
                    "http://session-service:8000/api/monitoring/increment",
                    params={"metric_name": "sold"}
                )
                if response1.status_code == 200 and response2.status_code == 200:
                    logger.info("Metrics 'payment_success' and 'sold' updated successfully")
            except Exception as e:
                logger.warning(f"Failed to update metrics: {e}")
            
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
def refund_payment(request: RefundRequest):
    """Вернуть деньги за билет"""
    logger.info(f"Refund requested for ticket {request.ticket_id}, reason: {request.reason}")
    
    try:
        # Отменяем билет напрямую через ticket-service
        cancel_ticket(request.ticket_id)
        logger.info(f"Ticket {request.ticket_id} cancelled successfully")
        
        logger.info(f"Refund successful for ticket {request.ticket_id}")
        
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