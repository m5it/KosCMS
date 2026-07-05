package com.example;

import java.util.*;

public class UserService {
    private final List<User> users;
    private final DatabaseConnection db;
    
    public UserService(DatabaseConnection db) {
        this.db = db;
        this.users = new ArrayList<>();
    }
    
    @Override
    public String toString() {
        return "UserService{users=" + users.size() + "}";
    }
    
    @Deprecated // MODIFIED: Marked for removal in v3.0
    public User findById(int id) {
        return users.stream()
            .filter(u -> u.getId() == id)
            .findFirst()
            .orElse(null);
    }
    
    public List<User> getAllUsers() {
        return Collections.unmodifiableList(users);
    }
}