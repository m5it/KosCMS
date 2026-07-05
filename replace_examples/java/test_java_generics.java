package com.example;

import java.util.List;
import java.util.ArrayList;

public class GenericService<T> {
    private List<T> items;
    
    public GenericService() {
        this.items = new ArrayList<>();
    }
    
    // MODIFIED: Simplified with Java 8 streams
    public List<T> getItems() {
        return items.stream()
            .filter(Objects::nonNull)
            .collect(Collectors.toList());
    }
}