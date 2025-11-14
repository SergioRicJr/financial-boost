package com.financialboost.api.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import com.financialboost.api.domain.balance.Balance;

public interface BalanceRepository extends JpaRepository<Balance, Integer> {
    
}
