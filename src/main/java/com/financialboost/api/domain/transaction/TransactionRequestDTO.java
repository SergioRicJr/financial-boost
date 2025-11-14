package com.financialboost.api.domain.transaction;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import com.financialboost.api.domain.transaction.Transaction.Operation;
import com.financialboost.api.domain.transaction.Transaction.TransactionType;

public record TransactionRequestDTO(
    BigDecimal value,
    Operation operation,
    TransactionType type,
    LocalDateTime datetime,
    Integer categoryId
) {}
