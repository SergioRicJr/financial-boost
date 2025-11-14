package com.financialboost.api.domain.user;

public record RegisterDTO(
    String login, String password, UserRole role, String picture
) {}
