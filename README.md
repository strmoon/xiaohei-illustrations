# 小黑配图 Codex 插件

这是一个可直接导入 Codex 的插件市场仓库。插件会为中文文章规划并生成 16:9 的“小黑”怪诞手绘正文配图。

本仓库 fork 自 [helloianneo/ian-xiaohei-illustrations](https://github.com/helloianneo/ian-xiaohei-illustrations)，并在此基础上改造成 Codex 插件市场格式。感谢原作者的创作与分享。

## 从 Codex 添加

在 Codex 的“添加插件市场”窗口中填写：

- 来源：这个项目的 GitHub 仓库地址，或本项目的本地绝对路径
- Git 引用：使用仓库默认分支即可，例如 `main`
- 稀疏路径：留空

添加市场后，在“小黑配图”市场中安装 `xiaohei-illustrations` 插件，并新建一个任务使插件生效。

如果这个项目被放在另一个仓库的子目录中，才需要填写“稀疏路径”；其值应为从仓库根目录到本项目根目录的相对路径。

## 使用示例

- 为这篇中文文章设计并生成小黑正文配图
- 分析这篇文章适合在哪些位置配图
- 把这个观点画成一张小黑手绘解释图

插件默认调用 `https://codex.apiz.ai/v1/images/generations`，使用 OpenAI 兼容协议。密钥优先从 `OPENAI_API_KEY` 读取，也支持 `CODEX_AUTH_FILE`、`CODEX_HOME/auth.json` 或 `~/.codex/auth.json`。
