// package com.financialboost.api.infra.logging;

// import org.springframework.context.annotation.Bean;
// import org.springframework.context.annotation.Configuration;
// import org.springframework.web.filter.CommonsRequestLoggingFilter;

// @Configuration
// public class RequestLoggingConfig {

//     @Bean
//     public CommonsRequestLoggingFilter requestLoggingFilter() {
//         CommonsRequestLoggingFilter filter = new CommonsRequestLoggingFilter();
//         filter.setIncludeClientInfo(true);
//         filter.setIncludeQueryString(true);
//         filter.setIncludePayload(true);
//         filter.setIncludeHeaders(false); // coloque true se quiser logar headers
//         filter.setMaxPayloadLength(10000);
//         filter.setAfterMessagePrefix("REQUEST DATA : ");
//         return filter;
//     }
// }
