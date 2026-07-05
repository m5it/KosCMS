package com.example.utils;

public class Logger {
    private static boolean enabled = true;
    
    public static void log(String message) {
        if (enabled) {
            System.out.println("[LOG] " + message);
        }
    }
    
    public static void setEnabled(boolean value) {
        enabled = value;
    }
    
    // Utility methods
    public static String format(String template, Object... args) {
        return String.format(template, args);
    }
}

// MODIFIED: Added shutdown hook
class EndMarker {
    public static void main(String[] args) {
        System.out.println("End of Logger module");
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("Shutting down...");
        }));
    }
}