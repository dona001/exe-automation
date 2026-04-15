package com.aqbridge;

/**
 * Thrown when a Java Bridge API call fails.
 */
public class JavaBridgeException extends RuntimeException {

    private final String endpoint;

    public JavaBridgeException(String endpoint, String message) {
        super(String.format("JavaBridge /%s: %s", endpoint, message));
        this.endpoint = endpoint;
    }

    public String getEndpoint() {
        return endpoint;
    }
}
