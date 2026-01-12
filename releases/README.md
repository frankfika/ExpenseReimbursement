# Releases

此文件夹用于存放本地构建的安装包。

## 目录结构

```
releases/
├── v1.0.0/
│   ├── 报销助手-Installer.dmg    # macOS 安装包
│   └── 报销助手.exe               # Windows 安装包
└── README.md
```

## 使用方法

本地构建后，将生成的 DMG 和 EXE 文件复制到对应的版本目录：

```bash
# macOS
cp dist/报销助手-Installer.dmg releases/v1.0.0/

# Windows
copy dist\报销助手.exe releases\v1.0.0\
```

## 注意事项

- 正式发布请使用 GitHub Releases：https://github.com/frankfika/ExpenseReimbursement/releases
- 此文件夹仅用于本地测试和版本归档
