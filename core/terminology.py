"""Electronic engineering terminology database."""

import json
import re
from pathlib import Path

from .config import TERMS_FILE, ensure_dirs

# Built-in EE datasheet terminology (EN -> ZH)
DEFAULT_TERMS = {
    # 基本参数
    "Absolute Maximum Ratings": "绝对最大额定值",
    "Recommended Operating Conditions": "推荐工作条件",
    "Electrical Characteristics": "电气特性",
    "Typical Performance Characteristics": "典型性能特性",
    "Functional Block Diagram": "功能框图",
    "Pin Configuration": "引脚配置",
    "Pin Description": "引脚说明",
    "Application Information": "应用信息",
    "Package Information": "封装信息",
    "Ordering Information": "订购信息",
    "Revision History": "修订历史",
    "Table of Contents": "目录",

    # 半导体与器件
    "Latch-up": "闩锁效应",
    "ESD": "静电放电",
    "HBM": "人体模型",
    "CDM": "充电器件模型",
    "MM": "机器模型",
    "MOSFET": "金属氧化物半导体场效应管",
    "BJT": "双极结型晶体管",
    "JFET": "结型场效应管",
    "IGBT": "绝缘栅双极晶体管",
    "Schottky": "肖特基",
    "Zener": "齐纳",
    "Photodiode": "光电二极管",
    "Phototransistor": "光电晶体管",
    "Thyristor": "晶闸管",
    "TRIAC": "双向可控硅",
    "SCR": "可控硅整流器",

    # 放大器
    "Phase Margin": "相位裕度",
    "Gain Margin": "增益裕度",
    "Unity-Gain Bandwidth": "单位增益带宽",
    "Gain-Bandwidth Product": "增益带宽积",
    "Slew Rate": "压摆率",
    "Common-Mode Rejection Ratio": "共模抑制比",
    "CMRR": "共模抑制比",
    "Power Supply Rejection Ratio": "电源抑制比",
    "PSRR": "电源抑制比",
    "Input Offset Voltage": "输入失调电压",
    "Input Bias Current": "输入偏置电流",
    "Input Offset Current": "输入失调电流",
    "Open-Loop Gain": "开环增益",
    "Closed-Loop Gain": "闭环增益",
    "Differential Amplifier": "差分放大器",
    "Instrumentation Amplifier": "仪表放大器",
    "Operational Amplifier": "运算放大器",
    "Op-Amp": "运算放大器",
    "Voltage Follower": "电压跟随器",
    "Transimpedance Amplifier": "跨阻放大器",
    "Inverting Input": "反相输入",
    "Non-Inverting Input": "同相输入",
    "Rail-to-Rail": "轨到轨",
    "Headroom": "余量",
    "Output Swing": "输出摆幅",

    # 数据转换器
    "ADC": "模数转换器",
    "DAC": "数模转换器",
    "Resolution": "分辨率",
    "ENOB": "有效位数",
    "Effective Number of Bits": "有效位数",
    "SINAD": "信纳比",
    "SFDR": "无杂散动态范围",
    "THD": "总谐波失真",
    "SNR": "信噪比",
    "Signal-to-Noise Ratio": "信噪比",
    "Spurious-Free Dynamic Range": "无杂散动态范围",
    "Total Harmonic Distortion": "总谐波失真",
    "Differential Nonlinearity": "差分非线性",
    "DNL": "差分非线性",
    "Integral Nonlinearity": "积分非线性",
    "INL": "积分非线性",
    "Sample Rate": "采样率",
    "Sampling Rate": "采样率",
    "Nyquist": "奈奎斯特",
    "Oversampling": "过采样",
    "Decimation": "抽取",
    "Sigma-Delta": "Sigma-Delta",
    "Successive Approximation": "逐次逼近",
    "Pipeline ADC": "流水线ADC",
    "Flash ADC": "并行比较ADC",
    "Conversion Time": "转换时间",
    "Throughput Rate": "吞吐率",
    "Aperture Delay": "孔径延迟",
    "Aperture Jitter": "孔径抖动",

    # 电源
    "LDO": "低压差线性稳压器",
    "Low Dropout": "低压差",
    "Dropout Voltage": "压差",
    "Buck Converter": "降压转换器",
    "Boost Converter": "升压转换器",
    "Buck-Boost": "升降压",
    "Switching Frequency": "开关频率",
    "Duty Cycle": "占空比",
    "Efficiency": "效率",
    "Load Regulation": "负载调整率",
    "Line Regulation": "线性调整率",
    "Ripple": "纹波",
    "Output Ripple": "输出纹波",
    "Input Ripple": "输入纹波",
    "PSRR": "电源抑制比",
    "Soft Start": "软启动",
    "Inrush Current": "浪涌电流",
    "Current Limit": "电流限制",
    "Thermal Shutdown": "热关断",
    "Undervoltage Lockout": "欠压锁定",
    "UVLO": "欠压锁定",
    "Power Good": "电源就绪",
    "Enable Pin": "使能引脚",
    "Feedback": "反馈",
    "Compensation": "补偿",
    "Loop Compensation": "环路补偿",
    "Stability": "稳定性",
    "Transient Response": "瞬态响应",
    "Load Transient": "负载瞬态",
    "Line Transient": "线性瞬态",
    "Decoupling": "去耦",
    "Bypass Capacitor": "旁路电容",
    "Bulk Capacitor": "大容量电容",

    # 时钟与时序
    "Jitter": "抖动",
    "Phase Noise": "相位噪声",
    "Clock Jitter": "时钟抖动",
    "Period Jitter": "周期抖动",
    "Cycle-to-Cycle Jitter": "周期间抖动",
    "Phase-Locked Loop": "锁相环",
    "PLL": "锁相环",
    "Delay-Locked Loop": "延迟锁定环",
    "DLL": "延迟锁定环",
    "Oscillator": "振荡器",
    "Crystal Oscillator": "晶体振荡器",
    "MEMS Oscillator": "MEMS振荡器",
    "VCXO": "压控晶体振荡器",
    "TCXO": "温补晶体振荡器",
    "Setup Time": "建立时间",
    "Hold Time": "保持时间",
    "Propagation Delay": "传播延迟",
    "Rise Time": "上升时间",
    "Fall Time": "下降时间",
    "Transition Time": "转换时间",
    "Clock-to-Output": "时钟到输出延迟",

    # 接口与通信
    "SPI": "串行外设接口",
    "I2C": "集成电路总线",
    "UART": "通用异步收发器",
    "USB": "通用串行总线",
    "LVDS": "低电压差分信号",
    "RS-232": "RS-232",
    "RS-485": "RS-485",
    "CAN": "控制器局域网",
    "LIN": "局部互联网络",
    "MIPI": "移动产业处理器接口",
    "PCIe": "高速外设组件互连",
    "HDMI": "高清多媒体接口",
    "Ethernet": "以太网",
    "Baud Rate": "波特率",
    "Bit Rate": "比特率",
    "Throughput": "吞吐量",
    "Handshake": "握手",
    "Acknowledge": "应答",
    "NACK": "否定应答",
    "ACK": "确认应答",
    "Arbitration": "仲裁",
    "Protocol": "协议",
    "Frame": "帧",
    "Packet": "数据包",
    "Payload": "有效载荷",
    "Checksum": "校验和",
    "CRC": "循环冗余校验",
    "Parity": "奇偶校验",

    # 存储器
    "SRAM": "静态随机存取存储器",
    "DRAM": "动态随机存取存储器",
    "SDRAM": "同步动态随机存取存储器",
    "DDR": "双倍数据速率",
    "Flash": "闪存",
    "NOR Flash": "NOR闪存",
    "NAND Flash": "NAND闪存",
    "EEPROM": "电可擦除可编程只读存储器",
    "ROM": "只读存储器",
    "Access Time": "访问时间",
    "Read Cycle": "读周期",
    "Write Cycle": "写周期",
    "Page Size": "页大小",
    "Sector": "扇区",
    "Block": "块",
    "Wear Leveling": "磨损均衡",
    "Endurance": "耐久性",
    "Retention": "数据保持",

    # 信号处理
    "Bandwidth": "带宽",
    "Cutoff Frequency": "截止频率",
    "Corner Frequency": "转角频率",
    "Roll-off": "滚降",
    "Filter": "滤波器",
    "Low-Pass Filter": "低通滤波器",
    "High-Pass Filter": "高通滤波器",
    "Band-Pass Filter": "带通滤波器",
    "Notch Filter": "陷波滤波器",
    "Anti-Aliasing": "抗混叠",
    "Fourier Transform": "傅里叶变换",
    "FFT": "快速傅里叶变换",
    "Frequency Response": "频率响应",
    "Bode Plot": "波特图",
    "Transfer Function": "传递函数",
    "Impulse Response": "脉冲响应",
    "Step Response": "阶跃响应",
    "Settling Time": "稳定时间",
    "Overshoot": "过冲",
    "Undershoot": "下冲",
    "Ringing": "振铃",
    "Damping": "阻尼",
    "Resonance": "谐振",
    "Quality Factor": "品质因数",
    "Q Factor": "品质因数",

    # PCB与封装
    "Footprint": "封装",
    "Land Pattern": "焊盘图案",
    "Solder Mask": "阻焊层",
    "Silkscreen": "丝印层",
    "Via": "过孔",
    "Blind Via": "盲孔",
    "Buried Via": "埋孔",
    "Micro Via": "微孔",
    "Trace": "走线",
    "Plane": "平面层",
    "Ground Plane": "地平面",
    "Power Plane": "电源平面",
    "Impedance": "阻抗",
    "Characteristic Impedance": "特征阻抗",
    "Controlled Impedance": "受控阻抗",
    "Return Path": "回流路径",
    "Crosstalk": "串扰",
    "EMI": "电磁干扰",
    "EMC": "电磁兼容",
    "Shielding": "屏蔽",
    "Thermal Pad": "散热焊盘",
    "Thermal Via": "散热过孔",
    "Thermal Resistance": "热阻",
    "Junction Temperature": "结温",
    "Ambient Temperature": "环境温度",
    "Case Temperature": "壳温",
    "Derating": "降额",
    "SOA": "安全工作区",
    "Safe Operating Area": "安全工作区",

    # 数字逻辑
    "Logic Level": "逻辑电平",
    "Threshold Voltage": "阈值电压",
    "VOH": "输出高电平",
    "VOL": "输出低电平",
    "VIH": "输入高电平",
    "VIL": "输入低电平",
    "Fan-Out": "扇出",
    "Tri-State": "三态",
    "Open-Drain": "开漏",
    "Open-Collector": "集电极开路",
    "Push-Pull": "推挽",
    "Totem-Pole": "图腾柱",
    "Schmitt Trigger": "施密特触发器",
    "Hysteresis": "滞回",
    "Glitch": "毛刺",
    "Metastability": "亚稳态",
    "FPGA": "现场可编程门阵列",
    "CPLD": "复杂可编程逻辑器件",
    "ASIC": "专用集成电路",
    "Gate": "门",
    "Flip-Flop": "触发器",
    "Latch": "锁存器",
    "Register": "寄存器",
    "Counter": "计数器",
    "Decoder": "解码器",
    "Multiplexer": "多路复用器",
    "Demultiplexer": "多路解复用器",

    # 传感器
    "Sensor": "传感器",
    "Transducer": "换能器",
    "Thermocouple": "热电偶",
    "RTD": "热电阻",
    "Thermistor": "热敏电阻",
    "Strain Gauge": "应变片",
    "Accelerometer": "加速度计",
    "Gyroscope": "陀螺仪",
    "Magnetometer": "磁力计",
    "Pressure Sensor": "压力传感器",
    "Humidity Sensor": "湿度传感器",
    "Proximity Sensor": "接近传感器",
    "Hall Effect": "霍尔效应",
    "Piezoelectric": "压电",
    "Sensitivity": "灵敏度",
    "Accuracy": "精度",
    "Precision": "精密度",
    "Linearity": "线性度",
    "Hysteresis": "迟滞",
    "Repeatability": "重复性",
    "Resolution": "分辨率",
    "Dynamic Range": "动态范围",
    "Full Scale": "满量程",
    "Zero Offset": "零点偏移",
    "Span": "量程",
    "Calibration": "校准",

    # 常见缩写与单位
    "typ.": "典型值",
    "typ": "典型值",
    "min.": "最小值",
    "min": "最小值",
    "max.": "最大值",
    "max": "最大值",
    "RMS": "均方根",
    "pk-pk": "峰峰值",
    "peak-to-peak": "峰峰值",
    "dB": "分贝",
    "dBm": "dBm",
    "dBV": "dBV",
    "dBμV": "dBμV",
    "ppm": "百万分之一",
    "ppb": "十亿分之一",
    "LSB": "最低有效位",
    "MSB": "最高有效位",
    "Full-Scale": "满量程",
    "Half-Scale": "半量程",
    "Common Mode": "共模",
    "Differential Mode": "差模",
    "Single-Ended": "单端",
    "Differential": "差分",
    "Ground": "地",
    "Analog Ground": "模拟地",
    "Digital Ground": "数字地",
    "Signal Ground": "信号地",
    "Chassis Ground": "机壳地",
    "Star Ground": "星形接地",
    "Ground Loop": "接地环路",
    "Star Connection": "星形连接",
    "Delta Connection": "三角形连接",
}


class TerminologyDB:
    """Manage electronic engineering terminology."""

    def __init__(self):
        self.terms: dict[str, str] = {}
        self._load()

    def _load(self):
        """Load terms from file, falling back to defaults."""
        self.terms = DEFAULT_TERMS.copy()
        if TERMS_FILE.exists():
            try:
                with open(TERMS_FILE, "r", encoding="utf-8") as f:
                    user_terms = json.load(f)
                self.terms.update(user_terms)
            except (json.JSONDecodeError, IOError):
                pass

    def save(self):
        """Save user-customized terms to file."""
        ensure_dirs()
        # Only save terms that differ from defaults
        user_terms = {
            k: v for k, v in self.terms.items()
            if k not in DEFAULT_TERMS or DEFAULT_TERMS[k] != v
        }
        with open(TERMS_FILE, "w", encoding="utf-8") as f:
            json.dump(user_terms, f, indent=2, ensure_ascii=False)

    def add_term(self, en: str, zh: str):
        """Add or update a term."""
        self.terms[en] = zh
        self.save()

    def remove_term(self, en: str):
        """Remove a term."""
        if en in self.terms:
            del self.terms[en]
            self.save()

    def lookup(self, text: str) -> list[tuple[str, str, int, int]]:
        """Find all term matches in text.

        Returns list of (en_term, zh_translation, start_pos, end_pos).
        Sorted by match length descending (longest match first).
        """
        text_lower = text.lower()
        matches = []

        # Fast path: regex scan all terms at once, O(text_length)
        # Build a reverse map: lower_term -> (original_term, zh)
        term_map: dict[str, tuple[str, str]] = {}
        for en, zh in self.terms.items():
            en_lower = en.lower()
            if en_lower not in term_map or len(en) > len(term_map[en_lower][0]):
                term_map[en_lower] = (en, zh)

        if not term_map:
            return []

        # Sort by length descending so longer matches take priority
        sorted_terms = sorted(term_map.keys(), key=len, reverse=True)
        pattern = "|".join(re.escape(t) for t in sorted_terms)
        for m in re.finditer(pattern, text_lower):
            term_key = m.group()
            en, zh = term_map[term_key]
            matches.append((en, zh, m.start(), m.end()))

        matches.sort(key=lambda m: m[3] - m[2], reverse=True)
        return matches

    def apply_terms(self, text: str) -> tuple[str, list[tuple[str, str]]]:
        """Replace known terms in text with their translations.

        Returns (processed_text, list_of_applied_terms).
        """
        matches = self.lookup(text)
        applied = []
        replaced_ranges = []

        for en, zh, start, end in matches:
            # Skip if this range overlaps with an already-replaced range
            overlap = False
            for rs, re in replaced_ranges:
                if start < re and end > rs:
                    overlap = True
                    break
            if overlap:
                continue
            applied.append((en, zh))
            replaced_ranges.append((start, end))

        # Apply replacements from end to start to preserve positions
        replaced_ranges.sort(key=lambda r: r[0], reverse=True)
        result = text
        for start, end in replaced_ranges:
            en_term = text[start:end]
            zh_term = self.terms.get(en_term, self.terms.get(en_term.lower(), ""))
            if zh_term:
                result = result[:start] + zh_term + result[end:]

        return result, applied

    def reset_to_defaults(self):
        """Reset all terms to built-in defaults, deleting user customizations."""
        self.terms = DEFAULT_TERMS.copy()
        if TERMS_FILE.exists():
            TERMS_FILE.unlink()

    def get_all_terms(self) -> dict[str, str]:
        """Return all terms."""
        return self.terms.copy()
