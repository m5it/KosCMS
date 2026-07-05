package com.example;

import org.junit.Test;
import static org.junit.Assert.*;

public class CalculatorTest {
    
    @Test(timeout = 1000) // MODIFIED: Added timeout
    public void testAddition() {
        Calculator calc = new Calculator();
        assertEquals(5, calc.add(2, 3));
    }
    
    @Override
    public String toString() {
        return "CalculatorTest{}";
    }
}

class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}