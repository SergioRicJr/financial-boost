package com.financialboost.api.domain.category;

import java.util.UUID;

public record CategoryResponseDTO(Integer id, String name, String icon, UUID userId) {
    public CategoryResponseDTO(Category category){
        this(category.getId(), category.getName(), category.getIcon(), category.getUser().getId());
    }
}
