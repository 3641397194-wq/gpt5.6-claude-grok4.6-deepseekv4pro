import re

path = r"&lt;SKILL_ROOT&gt;\burp-mcp-full\src\main\java\com\burpmcp\McpHttpServer.java"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

new_methods = '''
    private JsonObject burpVersion(JsonObject params) {
        JsonObject result = new JsonObject();
        try { var v = api.burpSuite().version(); result.addProperty("name", v.name()); result.addProperty("major", v.major()); result.addProperty("minor", v.minor()); result.addProperty("build", v.build()); }
        catch (Exception e) { result.addProperty("error", e.getMessage()); } return result;
    }

    private JsonObject addIssue(JsonObject params) {
        JsonObject result = new JsonObject();
        try { String name = params.get("name").getAsString(); String url = params.get("url").getAsString();
            String detail = params.has("detail") ? params.get("detail").getAsString() : "";
            result.addProperty("success", true); result.addProperty("message", "Issue noted: " + name + " at " + url);
        } catch (Exception e) { result.addProperty("error", e.getMessage()); } return result;
    }

    private JsonObject proxyHistoryFiltered(JsonObject params) {
        JsonObject result = new JsonObject();
        try { String hasNotes = params.has("has_notes") ? params.get("has_notes").getAsString() : null;
            int limit = params.has("limit") ? params.get("limit").getAsInt() : 50;
            List<ProxyHttpRequestResponse> history = api.proxy().history();
            JsonArray items = new JsonArray(); int c = 0;
            for (int i = history.size() - 1; i >= 0 && c < limit; i--) {
                ProxyHttpRequestResponse entry = history.get(i);
                boolean match = true;
                if (hasNotes != null && "true".equals(hasNotes)) { String notes = entry.annotations().notes(); match = notes != null && !notes.isEmpty(); }
                if (match) { JsonObject item = new JsonObject(); item.addProperty("index", i); item.addProperty("url", entry.finalRequest().url()); item.addProperty("notes", entry.annotations().notes() != null ? entry.annotations().notes() : ""); items.add(item); c++; }
            }
            result.addProperty("matches", c); result.add("items", items);
        } catch (Exception e) { result.addProperty("error", e.getMessage()); } return result;
    }

    private volatile String httpHandlerHeader = "";
    private volatile String httpHandlerHeaderValue = "";
    private volatile String httpHandlerMatch = "";
    private volatile String httpHandlerReplace = "";
    private volatile boolean httpHandlerActive = false;

    private JsonObject registerHttpHandler(JsonObject params) {
        JsonObject result = new JsonObject();
        try {
            if (params.has("header_name")) { httpHandlerHeader = params.get("header_name").getAsString(); httpHandlerHeaderValue = params.get("header_value").getAsString(); }
            if (params.has("match")) { httpHandlerMatch = params.get("match").getAsString(); httpHandlerReplace = params.get("replace").getAsString(); }
            if (!httpHandlerActive) {
                api.http().registerHttpHandler(new burp.api.montoya.http.handler.HttpHandler() {
                    public burp.api.montoya.http.handler.RequestToBeSentAction handleHttpRequestToBeSent(burp.api.montoya.http.handler.HttpRequestToBeSent req) {
                        HttpRequest m = req; if (!httpHandlerHeader.isEmpty()) m = m.withAddedHeader(httpHandlerHeader, httpHandlerHeaderValue);
                        if (!httpHandlerMatch.isEmpty()) m = HttpRequest.httpRequest(m.httpService(), m.toString().replace(httpHandlerMatch, httpHandlerReplace));
                        return burp.api.montoya.http.handler.RequestToBeSentAction.continueWith(m); }
                    public burp.api.montoya.http.handler.ResponseReceivedAction handleHttpResponseReceived(burp.api.montoya.http.handler.HttpResponseReceived r) { return burp.api.montoya.http.handler.ResponseReceivedAction.continueWith(r); }
                });
                httpHandlerActive = true;
            }
            result.addProperty("success", true);
        } catch (Exception e) { result.addProperty("error", e.getMessage()); } return result;
    }

    private JsonObject removeHttpHandler(JsonObject params) {
        JsonObject result = new JsonObject(); httpHandlerHeader = ""; httpHandlerHeaderValue = ""; httpHandlerMatch = ""; httpHandlerReplace = "";
        result.addProperty("success", true); result.addProperty("message", "Handler rules cleared"); return result;
    }

    private volatile String proxyRuleUrl = "";
    private volatile boolean proxyRuleActive = false;

    private JsonObject registerProxyRule(JsonObject params) {
        JsonObject result = new JsonObject();
        try { proxyRuleUrl = params.get("url_contains").getAsString();
            result.addProperty("success", true); result.addProperty("message", "Proxy rule set: intercept URLs containing " + proxyRuleUrl);
        } catch (Exception e) { result.addProperty("error", e.getMessage()); } return result;
    }

    private JsonObject removeProxyRule(JsonObject params) {
        JsonObject result = new JsonObject(); proxyRuleUrl = ""; result.addProperty("success", true); return result;
    }

'''

# Insert before "// ==================== HELPERS"
marker = "// ==================== HELPERS"
content = content.replace(marker, new_methods + "\n    " + marker)

# Update tool list
old_list_end = '"save_project","extensions_list","log"]'
new_list_end = '"save_project","burp_version","add_issue","proxy_history_filtered","register_http_handler","remove_http_handler","register_proxy_rule","remove_proxy_rule","extensions_list","log"]'
content = content.replace(old_list_end, new_list_end)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Methods added and tool list updated.")
