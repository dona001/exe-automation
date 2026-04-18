package com.aqbridge.te;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Manages the AQTEServer.exe lifecycle — start before tests, stop after.
 *
 * <pre>{@code
 * try (TEBridgeServer server = new TEBridgeServer("C:/tools/AQTEServer.exe")) {
 *     server.start();
 *     TEApp te = server.connect();
 *     te.startSession("session.ws");
 *     te.fillField(10, 20, "MYUSER");
 *     te.pressEnter();
 * }
 * }</pre>
 */
public class TEBridgeServer implements AutoCloseable {

    private final String exePath;
    private final int port;
    private final String baseUrl;
    private Process process;

    public TEBridgeServer(String exePath) {
        this(exePath, 9995);
    }

    public TEBridgeServer(String exePath, int port) {
        this.exePath = exePath;
        this.port = port;
        this.baseUrl = "http://localhost:" + port;
    }

    /** Start the AQTEServer.exe and wait until ready. */
    public void start() {
        start(30);
    }

    /** Start with custom timeout. */
    public void start(int timeoutSeconds) {
        if (isRunning()) {
            System.out.println("[TEBridge] Server already running on port " + port);
            return;
        }

        File exe = new File(exePath);
        if (!exe.exists()) {
            throw new TEBridgeException("start", "AQTEServer.exe not found at: " + exePath);
        }

        try {
            System.out.println("[TEBridge] Starting " + exePath);
            ProcessBuilder pb = new ProcessBuilder(exePath);
            pb.directory(exe.getParentFile());
            pb.redirectErrorStream(true);
            pb.redirectOutput(ProcessBuilder.Redirect.DISCARD);
            process = pb.start();
        } catch (IOException e) {
            throw new TEBridgeException("start", "Failed to launch: " + e.getMessage());
        }

        System.out.println("[TEBridge] Waiting for server...");
        long deadline = System.currentTimeMillis() + (timeoutSeconds * 1000L);
        while (System.currentTimeMillis() < deadline) {
            if (isRunning()) {
                System.out.println("[TEBridge] Server ready on " + baseUrl);
                return;
            }
            try { Thread.sleep(1000); } catch (InterruptedException e) {
                Thread.currentThread().interrupt(); break;
            }
        }
        stop();
        throw new TEBridgeException("start", "Server did not start within " + timeoutSeconds + "s");
    }

    /** Check if server is responding. */
    public boolean isRunning() {
        try {
            HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/te/ping"))
                    .timeout(Duration.ofSeconds(2)).GET().build();
            HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
            return resp.body().contains("pingstatus");
        } catch (Exception e) {
            return false;
        }
    }

    /** Get a connected TEApp client. */
    public TEApp connect() {
        return new TEApp(baseUrl);
    }

    /** Get a connected TEApp client with custom timeout. */
    public TEApp connect(int timeoutSeconds) {
        return new TEApp(baseUrl, timeoutSeconds);
    }

    /** Stop the server process. */
    public void stop() {
        if (process != null && process.isAlive()) {
            System.out.println("[TEBridge] Stopping server...");
            process.destroyForcibly();
            try { process.waitFor(5, java.util.concurrent.TimeUnit.SECONDS); } catch (Exception e) {}
            System.out.println("[TEBridge] Server stopped");
        }
        process = null;
    }

    public String getBaseUrl() { return baseUrl; }
    public int getPort() { return port; }

    @Override
    public void close() { stop(); }
}
