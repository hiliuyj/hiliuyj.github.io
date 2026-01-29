# CMSIS-DAP 技术方案与实现指南

## 目录

1. [技术方案概览](#1-技术方案概览)
2. [基础实现方案](#2-基础实现方案)
3. [SPI加速方案](#3-spi加速方案)
4. [高级优化方案](#4-高级优化方案)


---

## 1. 技术方案概览

### 1.1 实现方案分类

| 方案类型 | 性能等级 | 成本范围 | 技术复杂度 | 适用场景 |
|---------|----------|----------|------------|----------|
| 基础Bit-bang | 低 | $5-15 | 低 | 学习验证 |
| SPI硬件加速 | 中高 | $15-35 | 中 | 专业应用 |
| DMA并行传输 | 高 | $25-50 | 进阶 | 高性能 |
| FPGA实现 | 极高 | $80-150 | 商业级 | 顶级 |

### 1.2 技术路线图

基础级 → 进阶级 → 专业级 → 商业级
   ↓         ↓         ↓
Bit-bang → SPI加速 → DMA并行 → FPGA
   ↓         ↓         ↓
1MHz     → 10MHz   → 50MHz   → 100MHz+

---

## 2. 基础实现方案

### 2.1 Free-DAP (入门级推荐)

**特点:**
- 开源许可: BSD-3-Clause
- 代码量: ~2000行核心代码
- 内存占用: <16KB Flash, <2KB RAM

**核心优势:**
- 易于移植到各种MCU平台
- 完整的SWD和JTAG支持
- 活跃社区支持

**资源链接:**
- GitHub仓库: https://github.com/ataradov/free-dap
- 文档: https://ataradov.github.io/free-dap/
- 二进制文件: https://github.com/ataradov/free-dap/blob/master/bin/free_dap_rp2040.uf2

### 2.2 RP2040实现 (快速入门)

**硬件需求:**
- 树莓派Pico ($4-5)
- USB Type-C线
- 连接线

**引脚配置:**
```c
#define PIN_SWCLK_TCK   11
#define PIN_SWDIO_TMS   12
#define PIN_TDI        13
#define PIN_TDO        14
#define PIN_nRESET     15
```

---

## 3. SPI加速方案

### 3.1 STM32F405 DAP405 (SPI加速)

**核心创新:**
- 利用STM32 SPI外设实现JTAG/SWD时序
- 双向SPI控制解决SWDIO问题
- USB 2.0 High-Speed接口

**技术特点:**
- 时钟频率: 10-20MHz (vs 传统1-2MHz)
- 下载速度: 500-800KB/s
- CPU占用率降低80%

**关键代码实现:**

```c
// SPI双向控制函数
void SPI_SwitchPhaseToWrite(void) {
    SPI1->CR1 &= ~SPI_CR1_BIDIMODE;  // 输出模式
    SPI1->CR1 |= SPI_CR1_BIDIOE;    // 启用双向
}
void SPI_SwitchPhaseToListen(void) {
    SPI1->CR1 |= SPI_CR1_BIDIMODE;   // 输入模式
    SPI1->CR1 &= ~SPI_CR1_BIDIOE;    // 禁用双向输出
}

// SWD传输核心函数
uint8_t SWD_Transfer_LL(uint32_t request, uint32_t *data) {
    // 构建请求数据包
    uint8_t writeReq = (request & 0x0F) | ((generate_parity(request & 0x0F) << 4));

    // 请求阶段 (8位)
    SPI_SwitchPhaseToWrite();
    SPI_TMS_Transfer(writeReq, 8);

    // Turnaround阶段
    SPI_SwitchPhaseToListen();
    uint8_t ack = ListenToLine(DAP_Data.swd_conf.turnaround);

    if(ack == DAP_TRANSFER_OK) {
        // 数据阶段
        *data = SWDIO_Read(34);  // 32位数据 + 1位奇偶校验 + 1位turnaround
    }

    return ack;
}
```

**资源链接:**
- 项目地址: https://github.com/SushiBits/DAP405
- 硬件设计: https://github.com/SushiBits/DAP405/tree/master/hardware
- 技术文档: 包含在项目README中

### 3.2 Şahin Duran的SPI优化方案

**技术创新点:**

1. **分块传输优化:**

```c
void calculate_xfer_sizes(uint16_t input_len, uint8_t *buff) {
    // 将n位传输分解为SPI兼容块
    int isunAligned = input_len % 8 < 4 && input_len % 8 != 0;
    int isGreaterThan8 = input_len > 8;

    if(isunAligned && isGreaterThan8) {
        buff[IDX_8_BIT] = input_len / 8 - 2;  // 8位块
        buff[IDX_RM1_BIT] = 4;             // 4位余数
        buff[IDX_RM2_BIT] = input_len - buff[IDX_8_BIT]*8 - buff[IDX_RM1_BIT];
    }
    // ... 其他情况处理
}
```

2. **精确时序控制:**
   - ACK检测优化
   - WAIT/FAULT响应处理
   - 低频稳定性改进

**资源链接:**
- 技术文章: https://medium.com/@sahin.duran.9275/cmsis-dap-compliant-debug-probe-9236206d2bf8
- 源码仓库: https://github.com/saahinduran/STM32-JTAG-Emulator-
- 演示视频: https://www.youtube.com/watch?v=F0JFuAMPzhQ

---

## 4. 高级优化方案

### 4.1 STM32 DMA+GPIO并行传输

**理论基础:** 基于ST AN4666应用笔记
- 16位GPIO并行输出
- DMA控制器自动传输
- 理论最高50MHz并行传输

**核心实现:**

```c
// DMA配置用于并行传输
typedef struct {
    uint16_t gpio_mask;
    uint8_t clk_cycles;
    uint32_t data_buffer;
} parallel_xfer_t;

void DMA_ConfigForParallel(void) {
    DMA1_Stream0->CR = DMA_SxCR_CHSEL_0 |
                       DMA_SxCR_MSIZE_16BIT |
                       DMA_SxCR_MINC_ENABLE;
    DMA1_Stream0->PAR = (uint32_t)&GPIOB->ODR;
    DMA1_Stream0->M0AR = (uint32_t)parallel_data;
    DMA1_Stream0->FCR = DMA_SxFCR_DMDIS;
}
```

**资源链接:**
- 应用笔记: https://www.st.com/resource/en/application_note/an4666-parallel-synchronous-transmission-using-gpio-and-dma-stmicroelectronics.pdf
- ST社区讨论: https://community.st.com/t5/stm32-mcus-products/stm32-stm32f103c8t6-dma-performance-vs-bitbang/td-p/434106

### 4.2 FPGA方案

**技术特点:**
- USB 3.0 SuperSpeed (5Gbps)
- 硬件JTAG状态机
- 可达100MHz+时钟频率

**实现框架:**

```verilog
// FPGA JTAG状态机示例
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
    end else begin
        case (state)
            IDLE: if (tms) state <= SHIFT_DR;
            SHIFT_DR: if (count == 4) state <= CAPTURE_DR;
            CAPTURE_DR: state <= EXIT1_DR;
            // ... 其他状态
        endcase
    end
end
```

**资源链接:**
- Artecit FPGA方案: https://www.artekit.eu/products/debug/ak-cmsis-dap/
- DSTREAM-ST参考: https://www.arm.com/products/development-tools/debug-probes/dstream-st

---

