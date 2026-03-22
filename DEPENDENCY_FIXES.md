# 依赖项安全修复 (Dependency Security Fixes)

## 修复概述

本次修复针对 GitHub Security Alert 报告的 40+ 个已知 CVE 漏洞依赖项进行升级。

---

## Python 依赖修复 (requirements.txt)

### 修复的依赖项列表

| 依赖 | 原版本 | 修复版本 | CVE 编号 | 严重程度 |
|------|--------|---------|---------|---------|
| aiohttp | 3.8.5 | >=3.9.4 | CVE-2024-30251, CVE-2025-69223 | High |
| certifi | 2023.7.22 | >=2024.7.4 | CVE-2024-39689 | Low |
| dnspython | 2.3.0 | >=2.6.1 | CVE-2023-29483 | Moderate |
| h11 | 0.14.0 | >=0.16.0 | CVE-2025-43859 | **Critical** |
| idna | 3.4 | >=3.7 | CVE-2024-3651 | Moderate |
| Jinja2 | 3.1.2 | >=3.1.5 | CVE-2024-34064, CVE-2025-27516 | Moderate |
| pydantic | 2.1.1 | >=2.4.0 | CVE-2024-3772 | Moderate |
| python-multipart | 0.0.6 | >=0.0.18 | CVE-2024-53981, CVE-2026-24486 | High |
| requests | 2.31.0 | >=2.32.0 | CVE-2024-35195, CVE-2024-47081 | Moderate |
| starlette | 0.27.0 | >=0.40.0 | CVE-2024-47874, CVE-2025-54121 | High |
| tqdm | 4.66.1 | >=4.66.3 | CVE-2024-34062 | Low |
| urllib3 | 2.0.4 | >=2.2.2 | CVE-2025-66418, CVE-2025-66471 | High |
| zipp | 3.15.0 | >=3.19.1 | CVE-2024-5569 | Moderate |
| orjson | 3.9.5 | >=3.11.5 | security update | - |

### 安装更新后的依赖

```bash
cd server
pip install -r requirements.txt --upgrade
```

---

## Node.js 依赖修复 (client/package-lock.json)

### 自动修复方法

```bash
cd client

# 自动修复所有可修复的漏洞
npm audit fix --force

# 检查修复结果
npm audit
```

### 关键依赖升级列表

| 依赖 | 修复版本 | CVE | 严重程度 |
|------|---------|-----|---------|
| axios | ^1.7.4 | CVE-2024-39338 | High |
| express | ^4.20.0 | CVE-2024-43796 | Low |
| body-parser | ^1.20.3 | CVE-2024-45590 | High |
| webpack | ^5.94.0 | CVE-2025-68458 | Low |
| ws | ^8.17.1 | CVE-2024-37890 | High |
| ejs | ^3.1.10 | CVE-2024-33883 | Moderate |
| form-data | ^4.0.4 | CVE-2025-7783 | **Critical** |
| micromatch | ^4.0.8 | CVE-2024-4067 | Moderate |
| cross-spawn | ^7.0.5 | CVE-2024-21538 | High |
| node-forge | ^1.3.2 | CVE-2025-12816 | High |

### 手动修复（如自动修复失败）

```bash
cd client
npm install axios@1.7.4 webpack@5.94.0 express@4.20.0 body-parser@1.20.3 ws@8.17.1 ejs@3.1.10 form-data@4.0.4
```

---

## 验证修复

### Python

```bash
cd server
pip install pip-audit
pip-audit -r requirements.txt
```

### Node.js

```bash
cd client
npm audit
```

---

## 参考链接

- [GitHub Security Advisories](https://github.com/advisories)
- [CVE Details](https://www.cvedetails.com/)
- [Python Safety DB](https://pyup.io/safety/)
