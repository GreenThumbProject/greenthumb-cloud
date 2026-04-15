package io.greenthumb.auth.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * JPA entity mirroring the {@code app_user} PostgreSQL table.
 *
 * <p>Matches the SQLModel definition in {@code greenthumb_models/models.py}:
 * <ul>
 *   <li>{@code id_user}   — UUID primary key (generated on insert)</li>
 *   <li>{@code name}      — display name</li>
 *   <li>{@code email}     — unique login identifier</li>
 *   <li>{@code created_at}— auto-set on insert</li>
 * </ul>
 *
 * <p>The {@code password_hash} column exists in this service only — it is NOT
 * present in the Python SQLModel definition (auth is the sole writer).
 */
@Entity
@Table(name = "app_user")
@Data
@NoArgsConstructor
public class AppUser {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id_user", updatable = false, nullable = false)
    private UUID idUser;

    @Column(nullable = false)
    private String name;

    @Column(unique = true, nullable = false)
    private String email;

    /** BCrypt hash — stored only in auth-service, never exposed via API. */
    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}
