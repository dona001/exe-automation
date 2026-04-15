package com.aqbridge;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Manages the AQJavaServer.exe lifecycle — start before tests, stop after.
 *
 * <pre>{@code
 * // Auto-start and stop
 * JavaBridgeServer server = new JavaBridgeServer("C:/tools/AQJavaServer/AQJavaServer.exe");
 * server.start();   // launches EXE, waits for /ping to respond
 *
 * JavaApp app = server.connect();
 * app.activate("My App");
 * app.fill("Username", "admin");
 * app.click("Login");
 *
 * server.stop();    // kills the process
 *
 * // Or use try-with-resources (auto-stop)
 * try (JavaBridgeServer srv = new JavaBridgeServer("path/to/AQJavaServer.exe")) {
 *     srv.start();
 *     JavaApp app = srv.connect();
 *     app.activate("My App");
 *     // ... tests ...
 * } // server stops automatically
 * }</pre>
 */
public class JavaBridgeServer implements AutoCloseable {

    private final String exePath;
    private final int port;
    private final String baseUrl;
    private Process process;

    /**
     * Create a server manager pointing to the AQJavaServer.exe.
     *
     * @param exePath absolute path to AQJavaServer.exe
     */
    public JavaBridgeServer(String exePath) {
        this(exePath, 9996);
    }

    /**
     * Create a server manager with a custom port.
     *
     * @param exePath absolute path to AQJavaServer.exe
     * @param port    port number (default 9996)
     */
    public JavaBridgeServer(String exePath, int port) {
        this.exePath = exePath;
        this.port = port;
        this.baseUrl = "http://localhost:" + port;
    }

    /**
     * Start the AQJavaServer.exe and wait until it's ready.
     *
     * @throws JavaBridgeException if the server fails to start within 30 seconds
     */
    public void start() {
        start(30);
    }

    /**
     * Start the AQJavaServer.exe and wait until it's ready.
     *
     * @param timeoutSeconds max seconds to wait for the server to be ready
     */
    public void start(int timeoutSeconds) {
        if (isRunning()) {
            System.out.println("[JavaBridge] Server already running on port " + port);
            return;
        }

        File exe = new File(exePath);
        if (!exe.exists()) {
            throw new JavaBridgeException("start",
                    "AQJavaServer.exe not found at: " + exePath);
        }

        try {
            System.out.println("[JavaBridge] Starting " + exePath + " on port " + port);
            ProcessBuilder pb = new ProcessBuilder(exePath, String.valueOf(port));
            pb.directory(exe.getParentFile());
            pb.redirectErrorStream(true);
            // Don't inherit IO — let it run in background
            pb.redirectOutput(ProcessBuilder.Redirect.DISCARD);
            process = pb.start();
        } catch (IOException e) {
            throw new JavaBridgeException("start", "Failed to launch EXE: " + e.getMessage());
        }

        // Wait for server to be ready
        System.out.println("[JavaBridge] Waiting for server to be ready...");
        long deadline = System.currentTimeMillis() + (timeoutSeconds * 1000L);
        while (System.currentTimeMillis() < deadline) {
            if (isRunning()) {
                System.out.println("[JavaBridge] Server is ready on " + baseUrl);
                return;
            }
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        // Timeout — kill and throw
        stop();
        throw new JavaBridgeException("start",
                "Server did not start within " + timeoutSeconds + " seconds");
    }

    /**
     * Check if the server is running and responding.
     */
    public boolean isRunning() {
        try {
            HttpClient client = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(2))
                    .build();
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/aq/java/ping"))
                    .timeout(Duration.ofSeconds(2))
                    .GET()
                    .build();
            HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
            return resp.body().contains("ok");
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Get a JavaApp client connected to this server.
     */
    public JavaApp connect() {
        return new JavaApp(baseUrl);
    }

    /**
     * Get a JavaApp client with custom timeout.
     */
    public JavaApp connect(int timeoutSeconds) {
        return new JavaApp(baseUrl, timeoutSeconds);
    }

    /**
     * Stop the AQJavaServer.exe process.
     */
    public void stop() {
        if (process != null && process.isAlive()) {
            System.out.println("[JavaBridge] Stopping server...");
            process.destroyForcibly();
            try {
                process.waitFor(5, java.util.concurrent.TimeUnit.SECONDS);
            } catch (Exception e) {
                // ignore
            }
            System.out.println("[JavaBridge] Server stopped");
        }
        process = null;
    }

    /**
     * Get the base URL of the server.
     */
    public String getBaseUrl() {
        return baseUrl;
    }

    /**
     * Get the port number.
     */
    public int getPort() {
        return port;
    }

    /**
     * AutoCloseable — stops the server when used in try-with-resources.
     */
    @Override
    public void close() {
        stop();
    }
}
