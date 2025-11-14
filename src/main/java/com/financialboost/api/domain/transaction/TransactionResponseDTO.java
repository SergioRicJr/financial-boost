package com.financialboost.api.domain.transaction;

public record TransactionResponseDTO(
        Integer id,
        String categoryName,
        Integer categoryId,
        Transaction.Operation operation,
        Transaction.TransactionType type,
        String datetime,
        String value
) {
    public TransactionResponseDTO(Transaction transaction) {
        this(
            transaction.getId(),
            transaction.getCategory().getName(),
            transaction.getCategory().getId(),
            transaction.getOperation(),
            transaction.getType(),
            transaction.getDatetime().toString(),
            transaction.getValue().toString()
        );
    }
}
