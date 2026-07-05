package com.example;

import java.io.*;
import java.util.stream.Collectors;

public class FileProcessor {
    
    // MODIFIED: Modern try-with-resources
    public String readFile(String path) {
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            return br.lines().collect(Collectors.joining("\n"));
        } catch (FileNotFoundException e) {
            System.err.println("File not found: " + e.getMessage());
            return null;
        } catch (IOException e) {
            System.err.println("IO error: " + e.getMessage());
            return null;
        }
    }
}