# Deployment
Run `cp .env.example .env`, `make model`, `make build`, `make up`. Native C++ uses CPU-only CMake preset `cpu-diar`. First build requires Internet for dependencies. Pin model SHA/revision and runtime commit. Do not disable verification if download fails. Set strong API_TOKEN and TLS+identity-aware gateway for production. Both ports bind loopback by default.
