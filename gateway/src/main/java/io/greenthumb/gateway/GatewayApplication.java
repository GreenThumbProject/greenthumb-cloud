package io.greenthumb.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * GreenThumb API Gateway — Spring Cloud Gateway.
 *
 * <p>Routes all external traffic to the correct downstream service:
 * <pre>
 *   /auth/**      → auth-service    (port 8081)
 *   /accounts/**  → account-service (port 8082)
 *   /admin/**     → greenthumb-api  (port 8000)
 *   /sync/**      → greenthumb-api  (port 8000)
 * </pre>
 *
 * <p>Routing rules are defined in {@code application.yaml}. No business logic
 * lives here — the gateway is purely a reverse proxy.
 */
@SpringBootApplication
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}
