package com.financialboost.api.controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.financialboost.api.domain.user.AuthenticationDTO;
import com.financialboost.api.domain.user.LoginResponseDTO;
import com.financialboost.api.domain.user.RegisterDTO;
import com.financialboost.api.domain.user.User;
import com.financialboost.api.infra.security.TokenService;
import com.financialboost.api.repository.UserRepository;

@RestController
@RequestMapping("auth")
public class AuthenticationController {

    private static final User User = null;

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private UserRepository repository;

    @Autowired
    private TokenService tokenService;

    @PostMapping("/login")
    public ResponseEntity login(@RequestBody AuthenticationDTO body){
        var usernamePassword = new UsernamePasswordAuthenticationToken(body.login(), body.password());
        var auth = this.authenticationManager.authenticate(usernamePassword);

        var token = tokenService.generateToken((User) auth.getPrincipal());

        return ResponseEntity.ok(new LoginResponseDTO(token));
    }

    @PostMapping("/register")
    public ResponseEntity register(@RequestBody RegisterDTO body) {
        if(this.repository.findByLogin(body.login()) != null) return ResponseEntity.badRequest().build();

        String encryptedPassword = new BCryptPasswordEncoder().encode(body.password());
        User newUser = new User(body.login(), encryptedPassword, body.role(), body.picture());

        this.repository.save(newUser);

        return ResponseEntity.ok().build();
    }
}
