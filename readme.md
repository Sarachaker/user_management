# User Management API

A modern **FastAPI**-based microservice for user management, featuring:

- **User Registration & Authentication** (JWT-based)
- **Role-based Access Control** (Admin, Manager, Authenticated, Anonymous)
- **Email Verification** with token-based workflow
- **Password hashing** and **strength validation**
- **Profile picture URL validation**
- **Nickname generation** fallback
- **PostgreSQL** database integration (via SQLAlchemy Async + asyncpg)
- **Dockerized** for local development & production
- **Nginx** reverse-proxy configuration
- **Automated tests** with pytest & CI pipeline

---
## 🚀 Getting Started

1. **Clone the repository** (fork first if contributing):
   ```bash
   git clone https://github.com/<your‑org>/user_management_final_proj.git
   cd user_management_final_proj
   ```

2. **Environment**
   - Copy `.env.example` to `.env` and adjust settings (DB URL, secrets).

3. **Docker Compose**
   ```bash
   docker-compose up --build
   ```
   - FastAPI at `http://localhost:8000`
   - Nginx proxy at `http://localhost`
   - PgAdmin at `http://localhost:5050`

4. **Run tests**
   ```bash
   pytest
   ```

---
## 🛠️ Implemented Issue Fixes

| Issue | Description | Status |
|-------|-------------|--------|
| **[#1](https://github.com/Sarachaker/user_management/issues/2)**: Dockerfile libc-bin downgrade error | Allowed `--allow-downgrades` for glibc patch | ✔️ Fixed |
| **[#2](https://github.com/Sarachaker/user_management/issues/3)**: Profile picture URL validator | Ensured URLs end with `.jpg|.jpeg|.png` | ✔️ Fixed |
| **[#3](https://github.com/Sarachaker/user_management/issues/4)**: Nickname generation bypass | Always run generator when nickname missing | ✔️ Fixed |
| **[#4](https://github.com/Sarachaker/user_management/issues/5)**: Email verification role logic | Prevent `AUTHENTICATED` from re-verifying | ✔️ Fixed |
| **[#5](https://github.com/Sarachaker/user_management/issues/6)**: Weak password acceptance | Added Pydantic validator for strength rules | ✔️ Fixed |

---