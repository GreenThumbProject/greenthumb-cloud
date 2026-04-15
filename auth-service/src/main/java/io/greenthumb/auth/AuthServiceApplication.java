package io.greenthumb.auth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * GreenThumb Auth Service.
 *
 * <p>Adapted from the {@code hbrn-fastapi-template/auth-service} Spring Boot
 * project. GreenThumb-specific changes from the template:
 * <ul>
 *   <li>User entity uses {@code UUID id_user} (not auto-increment int)</li>
 *   <li>Table name is {@code app_user} (PostgreSQL reserves "user")</li>
 *   <li>JWT payload includes {@code id_user} (UUID) so the Python API can
 *       extract it via {@code GET /auth/validate} → {@code {"id_user": "..."}}</li>
 * </ul>
 *
 * <p>Endpoints exposed:
 * <ul>
 *   <li>{@code POST /auth/login}    — email + password → JWT</li>
 *   <li>{@code POST /auth/register} — create account (delegates to account-service)</li>
 *   <li>{@code GET  /auth/validate} — verify JWT, return {@code {id_user}}</li>
 *   <li>{@code GET  /actuator/health} — liveness probe</li>
 * </ul>
 */
@SpringBootApplication
public class AuthServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(AuthServiceApplication.class, args);
    }
}
