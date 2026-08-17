package com.burpmcp;

import burp.api.montoya.BurpExtension;
import burp.api.montoya.MontoyaApi;
import burp.api.montoya.logging.Logging;

/**
 * BurpSuite MCP Full Control Extension
 * Exposes ALL Burp functionality via MCP protocol on HTTP port 9876
 * 
 * Features:
 * - Proxy history access & filtering
 * - Intruder attack control (create, configure payloads, start, get results)
 * - Repeater tab management
 * - Scanner control
 * - Sitemap access
 * - Send HTTP requests through Burp
 * - Intercept control
 * - Encoding/decoding utilities
 */
public class BurpMcpExtension implements BurpExtension {

    private MontoyaApi api;
    private Logging logging;
    private McpHttpServer server;

    @Override
    public void initialize(MontoyaApi api) {
        this.api = api;
        this.logging = api.logging();

        api.extension().setName("MCP Full Control");

        try {
            server = new McpHttpServer(api, 9876);
            server.start();
            logging.logToOutput("[MCP] Server started on http://127.0.0.1:9876");
            logging.logToOutput("[MCP] Tools: proxy_history, send_request, intruder_attack, repeater, scanner, sitemap, intercept, encode/decode");
        } catch (Exception e) {
            logging.logToError("[MCP] Failed to start server: " + e.getMessage());
        }

        api.extension().registerUnloadingHandler(() -> {
            if (server != null) {
                server.stop();
                logging.logToOutput("[MCP] Server stopped");
            }
        });
    }
}
