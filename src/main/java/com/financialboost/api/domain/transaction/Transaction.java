package com.financialboost.api.domain.transaction;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import com.financialboost.api.domain.category.Category;
import com.financialboost.api.domain.user.User;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "transactions")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class Transaction {

    public Transaction(BigDecimal value, Operation operation, TransactionType type, LocalDateTime datetime, Category category, User user, String imgUrl){
        this.value = value;
        this.operation = operation;
        this.type = type;
        this.datetime = datetime;
        this.category = category;
        this.user = user;
        this.imgUrl = imgUrl;
    }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false)
    private BigDecimal value;

    @Enumerated(EnumType.ORDINAL)
    @Column(nullable = false)
    private Operation operation;

    @Enumerated(EnumType.ORDINAL)
    @Column(nullable = false)
    private TransactionType type;

    @Column(nullable = false)
    private LocalDateTime datetime;

    @ManyToOne
    @JoinColumn(name = "category_id", nullable = false)
    private Category category;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    private String imgUrl;

    public enum Operation {
        POSITIVE, // Representa entrada (+)
        NEGATIVE  // Representa saída (−)
    }

    public enum TransactionType {
        PIX,
        TED,
        DOC,
        TEF,
        BOLETO
    }
}