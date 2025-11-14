package com.financialboost.api.domain.balance;

import java.math.BigInteger;
import java.time.LocalDateTime;

public record BalanceRequestDTO(
    BigInteger value,
    LocalDateTime datetime,
    String userId
) {}
