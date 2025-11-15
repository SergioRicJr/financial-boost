package com.financialboost.api.controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

import jakarta.persistence.criteria.Predicate;

import com.financialboost.api.domain.category.Category;
import com.financialboost.api.domain.transaction.Transaction;
import com.financialboost.api.domain.transaction.Transaction.Operation;
import com.financialboost.api.domain.transaction.Transaction.TransactionType;
import com.financialboost.api.domain.transaction.TransactionRequestDTO;
import com.financialboost.api.domain.transaction.TransactionResponseDTO;
import com.financialboost.api.domain.transaction.TransactionUpdateDTO;
import com.financialboost.api.domain.user.User;
import com.financialboost.api.repository.CategoryRepository;
import com.financialboost.api.repository.TransactionRepository;
import com.financialboost.api.services.FileService;

@RestController
@RequestMapping("transactions")
public class TransactionController {
    @Autowired
    TransactionRepository repository;

    @Autowired
    CategoryRepository categoryRepository;

    @Autowired
    FileService fileService;

    private User getAuthenticatedUser() {
        return (User) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
    }

    @PostMapping(consumes = "multipart/form-data")
    public ResponseEntity<?> createTransaction(@ModelAttribute TransactionRequestDTO body) {
        User user = getAuthenticatedUser();

        Category category = categoryRepository.findById(body.categoryId())
                .filter(c -> c.getUser().getId().equals(user.getId()))
                .orElse(null);

        if (category == null) {
            return ResponseEntity.status(404).body("Categoria não encontrada");
        }

        String imgUrl = null;
        if (body.image() != null && !body.image().isEmpty()) {
            try {
                imgUrl = fileService.saveFile(body.image());
            } catch (IOException e) {
                return ResponseEntity.status(500).body("Erro ao salvar imagem: " + e.getMessage());
            }
        }

        Transaction transaction = new Transaction(
            body.value(),
            body.operation(),
            body.type(),
            body.datetime(),
            category,
            user,
            imgUrl
        );

        repository.save(transaction);
        return ResponseEntity.ok(new TransactionResponseDTO(transaction));
    }

    @GetMapping
    public ResponseEntity<Page<TransactionResponseDTO>> getAllTransactions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) TransactionType type,
            @RequestParam(required = false) Integer categoryId,
            @RequestParam(required = false) Operation operation,
            @RequestParam(required = false) BigDecimal valueMin,
            @RequestParam(required = false) BigDecimal valueMax,
            @RequestParam(required = false) LocalDateTime datetimeMin,
            @RequestParam(required = false) LocalDateTime datetimeMax) {
        User user = getAuthenticatedUser();

        Pageable pageable = PageRequest.of(page, size);

        Specification<Transaction> spec = buildSpecification(
                user.getId(), type, categoryId, operation,
                valueMin, valueMax, datetimeMin, datetimeMax);

        Page<Transaction> transactionPage = this.repository.findAll(spec, pageable);
        Page<TransactionResponseDTO> transactionResponsePage = transactionPage.map(TransactionResponseDTO::new);

        return ResponseEntity.ok(transactionResponsePage);
    }

    private Specification<Transaction> buildSpecification(
            UUID userId,
            TransactionType type,
            Integer categoryId,
            Operation operation,
            BigDecimal valueMin,
            BigDecimal valueMax,
            LocalDateTime datetimeMin,
            LocalDateTime datetimeMax) {
        return (root, query, cb) -> {
            Predicate predicate = cb.equal(root.get("user").get("id"), userId);

            if (type != null) {
                predicate = cb.and(predicate, cb.equal(root.get("type"), type));
            }

            if (categoryId != null) {
                predicate = cb.and(predicate, cb.equal(root.get("category").get("id"), categoryId));
            }

            if (operation != null) {
                predicate = cb.and(predicate, cb.equal(root.get("operation"), operation));
            }

            if (valueMin != null) {
                predicate = cb.and(predicate, cb.greaterThanOrEqualTo(root.get("value"), valueMin));
            }

            if (valueMax != null) {
                predicate = cb.and(predicate, cb.lessThanOrEqualTo(root.get("value"), valueMax));
            }

            if (datetimeMin != null) {
                predicate = cb.and(predicate, cb.greaterThanOrEqualTo(root.get("datetime"), datetimeMin));
            }

            if (datetimeMax != null) {
                predicate = cb.and(predicate, cb.lessThanOrEqualTo(root.get("datetime"), datetimeMax));
            }

            return predicate;
        };
    }


    @GetMapping("/{id}")
    public ResponseEntity<?> getTransactionById(@PathVariable Integer id) {
        User user = (User) SecurityContextHolder.getContext().getAuthentication().getPrincipal();

        Transaction transaction = repository.findById(id)
            .filter(c -> c.getUser().getId().equals(user.getId()))
            .orElse(null);

        if (transaction == null) {
            return ResponseEntity.status(404).body("Categoria não encontrada");
        }

        return ResponseEntity.ok(new TransactionResponseDTO(transaction));
    }

    @PutMapping(value = "/{id}", consumes = "multipart/form-data")
    public ResponseEntity<?> updateTransaction(@PathVariable Integer id, @ModelAttribute TransactionUpdateDTO body) {
        User user = getAuthenticatedUser();

        Transaction transaction = repository.findById(id)
            .filter(t -> t.getUser().getId().equals(user.getId()))
            .orElse(null);

        if (transaction == null) {
            return ResponseEntity.status(404).body("Transação não encontrada");
        }

        if (body.value() != null) {
            transaction.setValue(body.value());
        }

        if (body.operation() != null) {
            transaction.setOperation(body.operation());
        }

        if (body.type() != null) {
            transaction.setType(body.type());
        }

        if (body.datetime() != null) {
            transaction.setDatetime(body.datetime());
        }

        if (body.categoryId() != null) {
            Category category = categoryRepository.findById(body.categoryId())
                    .filter(c -> c.getUser().getId().equals(user.getId()))
                    .orElse(null);

            if (category == null) {
                return ResponseEntity.status(404).body("Categoria não encontrada");
            }

            transaction.setCategory(category);
        }

        if (body.image() != null && !body.image().isEmpty()) {
            try {
                String imgUrl = fileService.saveFile(body.image());
                transaction.setImgUrl(imgUrl);
            } catch (IOException e) {
                return ResponseEntity.status(500).body("Erro ao salvar imagem: " + e.getMessage());
            }
        }

        repository.save(transaction);
        return ResponseEntity.ok(new TransactionResponseDTO(transaction));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteTransaction(@PathVariable Integer id) {
        User user = (User) SecurityContextHolder.getContext().getAuthentication().getPrincipal();

        Transaction transaction = repository.findById(id)
            .filter(c -> c.getUser().getId().equals(user.getId()))
            .orElse(null);

        if (transaction == null) {
            return ResponseEntity.status(404).body("Categoria não encontrada");
        }

        repository.delete(transaction);
        return ResponseEntity.noContent().build(); // 204
    }
}
