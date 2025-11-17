package com.financialboost.api.repository;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import com.financialboost.api.domain.transaction.Transaction;
import com.financialboost.api.domain.transaction.Transaction.Operation;
import com.financialboost.api.domain.transaction.Transaction.TransactionType;

public interface TransactionRepository extends JpaRepository<Transaction, Integer> {
    Page<Transaction> findByUserId(UUID userId, Pageable pageable);

    @Query("""
        SELECT t FROM Transaction t
        WHERE t.user.id = :userId
          AND (:categoryId IS NULL OR t.category.id = :categoryId)
          AND (:valueMin IS NULL OR t.value >= :valueMin)
          AND (:valueMax IS NULL OR t.value <= :valueMax)
          AND (:type IS NULL OR t.type = :type)
          AND (:operation IS NULL OR t.operation = :operation)
          AND t.datetime >= COALESCE(:datetimeMin, t.datetime)
          AND t.datetime <= COALESCE(:datetimeMax, t.datetime)
        """)
    Page<Transaction> findByFilters(
            @Param("userId") UUID userId,
            @Param("type") TransactionType type,
            @Param("categoryId") Integer categoryId,
            @Param("operation") Operation operation,
            @Param("valueMin") BigDecimal valueMin,
            @Param("valueMax") BigDecimal valueMax,
            @Param("datetimeMin") LocalDateTime datetimeMin,
            @Param("datetimeMax") LocalDateTime datetimeMax,
            Pageable pageable);
}
