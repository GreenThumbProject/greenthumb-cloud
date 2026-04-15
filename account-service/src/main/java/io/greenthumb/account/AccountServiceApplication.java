package io.greenthumb.account;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * GreenThumb Account Service.
 *
 * <p>Handles CRUD for {@code app_user} records. Adapted from the
 * {@code hbrn-fastapi-template/account-service} Spring Boot project.
 *
 * <p>GreenThumb-specific changes from the template:
 * <ul>
 *   <li>User PK is {@code UUID id_user} (not int)</li>
 *   <li>Table is {@code app_user} (PostgreSQL reserves "user")</li>
 *   <li>Password hashing is delegated to auth-service — account-service
 *       accepts a plain password on registration, calls auth-service to hash
 *       it, and stores only the hash.</li>
 * </ul>
 *
 * <p>Endpoints exposed:
 * <ul>
 *   <li>{@code POST   /accounts}         — register a new user</li>
 *   <li>{@code GET    /accounts/{id}}    — get account by UUID</li>
 *   <li>{@code PATCH  /accounts/{id}}    — update name / email</li>
 *   <li>{@code DELETE /accounts/{id}}    — delete account</li>
 *   <li>{@code GET    /actuator/health}  — liveness probe</li>
 * </ul>
 */
@SpringBootApplication
public class AccountServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(AccountServiceApplication.class, args);
    }
}
