package com.financialboost.api.controllers;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.financialboost.api.domain.category.Category;
import com.financialboost.api.domain.category.CategoryRequestDTO;
import com.financialboost.api.domain.category.CategoryResponseDTO;
import com.financialboost.api.domain.user.User;
import com.financialboost.api.repository.CategoryRepository;

@RestController
@RequestMapping("categories")
public class CategoryController {
    @Autowired
    CategoryRepository repository;

    @PostMapping
    public ResponseEntity createCategory(@RequestBody CategoryRequestDTO body) {
        User user = (User) SecurityContextHolder.getContext().getAuthentication().getPrincipal();

        Category newCategory = new Category(body, user);

        this.repository.save(newCategory);
        return ResponseEntity.ok().build();
    }

    @GetMapping
    public ResponseEntity getAllCategoies() {
        User user = (User) SecurityContextHolder.getContext().getAuthentication().getPrincipal();

        List<CategoryResponseDTO> categoryList = 
            this.repository.findByUserId(user.getId())
                        .stream()
                        .map(CategoryResponseDTO::new)
                        .toList();

        return ResponseEntity.ok(categoryList);
    }


    @GetMapping("/{id}")
    public ResponseEntity getCategoryById(@PathVariable Integer id) {
        User user = (User) SecurityContextHolder.getContext().getAuthentication().getPrincipal();

        Category category = repository.findById(id)
            .filter(c -> c.getUser().getId().equals(user.getId()))
            .orElse(null);

        if (category == null) {
            return ResponseEntity.status(404).body("Categoria não encontrada");
        }

        return ResponseEntity.ok(new CategoryResponseDTO(category));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity deleteCategory(@PathVariable Integer id) {
        User user = (User) SecurityContextHolder.getContext().getAuthentication().getPrincipal();

        Category category = repository.findById(id)
            .filter(c -> c.getUser().getId().equals(user.getId()))
            .orElse(null);

        if (category == null) {
            return ResponseEntity.status(404).body("Categoria não encontrada");
        }

        repository.delete(category);
        return ResponseEntity.noContent().build(); // 204
    }
}
