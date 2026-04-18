package com.aqbridge.te;

/**
 * Thrown when a TE Bridge API call fails.
 */
public class TEBridgeException extends RuntimeException {

    private final String endpoint;

    public TEBridgeException(String endpoint, String message) {
        super(String.format("TEBridge /%s: %s", endpoint, message));
        this.endpoint = endpoint;
    }

    public String getEndpoint() {
        return endpoint;
    }
}
