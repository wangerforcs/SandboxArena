# Contributing benchmark results

Sandbox Arena 接受两类 PR：新增或修改 workload，以及提交某个 workload 的运行结果。

## 提交结果

1. Fork 仓库并运行一个已存在的 workload。
2. 把结果放到 `data/results/`，文件名包含 provider、workload 和日期。
3. 运行校验：

   ```bash
   python -m arena validate data/results/your-result.json
   python -m unittest discover -s tests -v
   ```

4. 提交 PR，并在描述中说明 provider 配置、区域、运行模式、重复次数和证据来源。

不要提交以下内容：

- API key、token、cookie、环境变量 dump；
- 私有仓库代码、私有数据或完整命令输出中的敏感信息；
- 没有 workload 版本号的手工改写结果；
- 把厂商官网数字伪装成独立实测的数据。

维护者可能要求重新运行，或将结果标为 `pending`，直到它能被复现或得到足够的运行上下文。

