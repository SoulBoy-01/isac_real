import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "D:/isac/outputs/sprinkler_demo_equipment_list";
const outputPath = "D:/isac/outputs/sprinkler_demo_equipment_list/OFDM_ISAC_室内喷淋Demo器材清单.xlsx";
const navy = "#17324D";
const teal = "#0F766E";
const sky = "#E0F2FE";
const mint = "#D1FAE5";
const amber = "#FEF3C7";
const rose = "#FEE2E2";
const gray = "#F3F4F6";
const border = "#CBD5E1";
const text = "#1F2937";
const white = "#FFFFFF";

const workbook = Workbook.create();
const procurement = workbook.worksheets.add("器材清单");
const parameters = workbook.worksheets.add("搭建参数");
const safety = workbook.worksheets.add("安全与验收");

function title(sheet, headline, subtitle, lastColumn) {
  sheet.mergeCells("A1:" + lastColumn + "1");
  sheet.getRange("A1").values = [[headline]];
  sheet.getRange("A1").format = {
    fill: navy,
    font: { bold: true, color: white, size: 16 },
    horizontalAlignment: "left",
    verticalAlignment: "center",
  };
  sheet.getRange("A1").format.rowHeight = 30;
  sheet.mergeCells("A2:" + lastColumn + "2");
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2").format = {
    fill: sky,
    font: { color: text, italic: true, size: 10 },
    horizontalAlignment: "left",
    verticalAlignment: "center",
    wrapText: true,
  };
  sheet.getRange("A2").format.rowHeight = 36;
}

function header(range) {
  range.format = {
    fill: teal,
    font: { bold: true, color: white, size: 10 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: border },
  };
  range.format.rowHeight = 34;
}

function data(range) {
  range.format = {
    font: { color: text, size: 10 },
    verticalAlignment: "top",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: border },
  };
}

title(
  procurement,
  "OFDM-ISAC 室内循环喷淋 Demo - 器材采购与搭建清单",
  "目标：在 3-5 m 固定视距链路中搭建低压、可循环、可重复的受控喷淋幕。主实验中天线与射频设备保持干燥，固定花洒向水箱回喷。价格为低预算估算，采购前请按实际平台复核。",
  "P"
);

procurement.getRange("A3:E3").values = [[
  "预算汇总（自动）", "最低预算（元）", null, "最高预算（元）", null,
]];
procurement.getRange("A3:E3").format = {
  fill: mint,
  font: { bold: true, color: text },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  borders: { preset: "all", style: "thin", color: border },
};
procurement.getRange("C3").formulas = [["=SUM(L6:L26)"]];
procurement.getRange("E3").formulas = [["=SUM(M6:M26)"]];
procurement.getRange("C3:E3").format.numberFormat = "¥#,##0";
procurement.mergeCells("A4:P4");
procurement.getRange("A4").values = [[
  "采购原则：优先采购“必需 + 纳入预算=是”的项目。水泵选择“低压潜水泵”或“低压自吸泵”其一即可；推荐低价潜水泵。水箱、水位和防溅罩在干燥/喷淋全部状态中必须保持不变。",
]];
procurement.getRange("A4").format = {
  fill: amber,
  font: { color: text, bold: true, size: 10 },
  wrapText: true,
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: border },
};
procurement.getRange("A4").format.rowHeight = 30;
procurement.getRange("A5:P5").values = [[
  "序号", "分层", "类别", "器材", "推荐规格 / 选型", "数量", "单位", "必需程度",
  "单价低估（元）", "单价高估（元）", "纳入预算", "小计低估（元）", "小计高估（元）",
  "用途 / 搭建位置", "注意事项", "采购状态",
]];
header(procurement.getRange("A5:P5"));

const items = [
  [1, "必需", "循环储水", "带盖塑料水箱", "50 L 左右；厚壁 PP/PE，带盖，建议带排水口", 1, "个", "必需", 60, 150, "是", null, null, "喷头向水箱回喷，形成循环水源", "水位在每次实验前标记；水箱全程固定在原位置", "未采购"],
  [2, "必需", "水泵（二选一）", "低压潜水泵", "12 V/24 V 小型潜水泵，约 3-8 L/min，扬程至少 2 m，进水口带滤网", 1, "台", "必需", 35, 100, "是", null, null, "推荐默认方案；直接放入水箱，将水送至花洒", "优先低压直流；电源和接头远离飞溅区", "未采购"],
  [3, "备选", "水泵（二选一）", "低压自吸泵", "12 V/24 V 隔膜自吸泵，约 3-5 L/min，可调压或带回流", 1, "台", "备选", 60, 180, "否", null, null, "可替代潜水泵；水泵置于水箱外", "需密封吸水管、进水滤网，且避免空转吸气", "未采购"],
  [4, "必需", "水路", "进水软管", "匹配水泵接口的 PVC/硅胶软管，建议 6-10 m，内径按泵口选择", 1, "卷", "必需", 20, 60, "是", null, null, "水泵至顶部固定花洒", "软管应固定于支架，避免摆动和滴水靠近设备", "未采购"],
  [5, "必需", "水路", "软管卡箍 / 快接头", "匹配软管内外径；建议备多个", 1, "套", "必需", 15, 45, "是", null, null, "密封水泵、软管和花洒接口", "先做 10 min 空载循环检漏", "未采购"],
  [6, "必需", "喷淋", "固定花洒喷头", "低压雨淋式、宽散射花洒；避免高压细雾和强水柱", 1, "个", "必需", 15, 60, "是", null, null, "安装在水箱正上方，向下回喷形成水滴幕", "必须固定在支架上，不可手持扫动", "未采购"],
  [7, "建议", "喷淋", "手动球阀 / 调节阀", "与软管接口匹配，建议 1 个", 1, "个", "建议", 10, 35, "是", null, null, "配合泵速形成低/中/高三个重复档位", "每档在实验前锁定阀门开度并拍照记录", "未采购"],
  [8, "建议", "喷淋", "量杯与计时器", "1 L 量杯 + 手机计时；可选低压水流量计", 1, "套", "建议", 10, 80, "是", null, null, "每档收集 60 s 水量，标定喷淋强度等级", "标签称“喷淋强度等级”，不称自然雨强 mm/h", "未采购"],
  [9, "必需", "结构", "非金属支架", "PVC 管架 / 塑料衣架 / 玻纤杆，喷头高度约 0.8-1.5 m", 1, "套", "必需", 30, 100, "是", null, null, "固定花洒并让水滴回落至水箱", "避免金属支架进入两天线主瓣和视距路径", "未采购"],
  [10, "必需", "结构", "扎带、夹具、胶带", "尼龙扎带、塑料夹具、防水胶带各适量", 1, "套", "必需", 15, 50, "是", null, null, "固定软管、喷头、支架和滴水方向", "软管不能松脱或靠近射频接头", "未采购"],
  [11, "建议", "防飞溅", "塑料挡水板 / 浴帘", "透明 PVC 挡水板或浴帘，覆盖水箱周边但不遮挡主瓣", 1, "套", "建议", 20, 80, "是", null, null, "降低回喷飞溅，保护天线周边", "从干燥基线开始就安装，不能只在喷淋时安装", "未采购"],
  [12, "建议", "防飞溅", "水箱上方格栅 / 塑料网", "塑料格栅或网片，开孔大于水滴直径", 1, "块", "建议", 10, 40, "是", null, null, "缓冲回水、减小水面飞溅", "避免遮挡水幕；保持位置固定", "未采购"],
  [13, "必需", "设备保护", "天线防溅罩", "固定非金属防溅罩或透明聚碳酸酯挡板", 2, "个", "必需", 20, 80, "是", null, null, "天线和馈线接头保持干燥", "所有状态均安装，不能只在喷淋状态加罩", "未采购"],
  [14, "必需", "设备保护", "地面防水垫 / 防滑垫", "防水、防滑，覆盖水箱与喷淋区下方", 1, "张", "必需", 30, 100, "是", null, null, "限制漏水范围并降低滑倒风险", "不能影响天线与水箱相对几何", "未采购"],
  [15, "必需", "电气安全", "低压直流电源", "与水泵匹配的 12 V/24 V 电源，留足电流余量", 1, "个", "必需", 40, 120, "是", null, null, "给低压水泵供电", "交流插座、插排和电源适配器置于干燥高处", "未采购"],
  [16, "建议", "电气安全", "带漏电保护的插座 / 漏保插头", "适用于室内临时用电", 1, "个", "建议", 45, 120, "是", null, null, "降低水泵电源侧漏电风险", "不能代替低压隔离和干湿分区", "未采购"],
  [17, "必需", "维护", "泵入口滤网", "细网滤罩或可拆洗滤网", 1, "个", "必需", 5, 25, "是", null, null, "防止杂物进入水泵与花洒", "每次实验后清洗，避免堵塞导致流量漂移", "未采购"],
  [18, "建议", "维护", "吸水海绵、抹布、收纳箱", "吸水性强；单独存放水路器材", 1, "套", "建议", 20, 60, "是", null, null, "处理滴水、结束后恢复干燥环境", "实验结束后确认天线与接头完全干燥", "未采购"],
  [19, "建议", "记录", "手机支架 / 摄像设备", "固定拍摄喷淋幕、阀门档位和水量标定过程", 1, "套", "建议", 20, 80, "否", null, null, "保存实验可追溯证据", "镜头同样置于防溅区外", "未采购"],
  [20, "建议", "标定", "卷尺、水平尺、记号笔", "至少卷尺 5 m、油性标记笔", 1, "套", "建议", 15, 50, "是", null, null, "记录天线间距、喷头高度、喷淋幕位置和水位", "每次实验复核几何，避免位置变化成为伪特征", "未采购"],
  [21, "可选升级", "喷淋均匀性", "第二个固定花洒 + 三通", "当单个花洒水幕宽度不足时使用", 1, "套", "可选", 25, 90, "否", null, null, "扩大水幕宽度，提高覆盖重复性", "先完成单喷头基线；升级后需重新标定所有等级", "未采购"],
];

procurement.getRange("A6:P26").values = items;
procurement.getRange("L6:L26").formulas = [
  ["=IF(K6=\"是\",F6*I6,0)"], ["=IF(K7=\"是\",F7*I7,0)"], ["=IF(K8=\"是\",F8*I8,0)"],
  ["=IF(K9=\"是\",F9*I9,0)"], ["=IF(K10=\"是\",F10*I10,0)"], ["=IF(K11=\"是\",F11*I11,0)"],
  ["=IF(K12=\"是\",F12*I12,0)"], ["=IF(K13=\"是\",F13*I13,0)"], ["=IF(K14=\"是\",F14*I14,0)"],
  ["=IF(K15=\"是\",F15*I15,0)"], ["=IF(K16=\"是\",F16*I16,0)"], ["=IF(K17=\"是\",F17*I17,0)"],
  ["=IF(K18=\"是\",F18*I18,0)"], ["=IF(K19=\"是\",F19*I19,0)"], ["=IF(K20=\"是\",F20*I20,0)"],
  ["=IF(K21=\"是\",F21*I21,0)"], ["=IF(K22=\"是\",F22*I22,0)"], ["=IF(K23=\"是\",F23*I23,0)"],
  ["=IF(K24=\"是\",F24*I24,0)"], ["=IF(K25=\"是\",F25*I25,0)"], ["=IF(K26=\"是\",F26*I26,0)"],
];
procurement.getRange("M6:M26").formulas = [
  ["=IF(K6=\"是\",F6*J6,0)"], ["=IF(K7=\"是\",F7*J7,0)"], ["=IF(K8=\"是\",F8*J8,0)"],
  ["=IF(K9=\"是\",F9*J9,0)"], ["=IF(K10=\"是\",F10*J10,0)"], ["=IF(K11=\"是\",F11*J11,0)"],
  ["=IF(K12=\"是\",F12*J12,0)"], ["=IF(K13=\"是\",F13*J13,0)"], ["=IF(K14=\"是\",F14*J14,0)"],
  ["=IF(K15=\"是\",F15*J15,0)"], ["=IF(K16=\"是\",F16*J16,0)"], ["=IF(K17=\"是\",F17*J17,0)"],
  ["=IF(K18=\"是\",F18*J18,0)"], ["=IF(K19=\"是\",F19*J19,0)"], ["=IF(K20=\"是\",F20*J20,0)"],
  ["=IF(K21=\"是\",F21*J21,0)"], ["=IF(K22=\"是\",F22*J22,0)"], ["=IF(K23=\"是\",F23*J23,0)"],
  ["=IF(K24=\"是\",F24*J24,0)"], ["=IF(K25=\"是\",F25*J25,0)"], ["=IF(K26=\"是\",F26*J26,0)"],
];
data(procurement.getRange("A6:P26"));
procurement.getRange("I6:M26").format.numberFormat = "¥#,##0";
procurement.getRange("K6:K26").dataValidation = { rule: { type: "list", values: ["是", "否"] } };
procurement.getRange("P6:P26").dataValidation = { rule: { type: "list", values: ["未采购", "已下单", "已到货", "已安装", "不采购"] } };
procurement.getRange("H6:H26").dataValidation = { rule: { type: "list", values: ["必需", "建议", "备选", "可选"] } };
procurement.getRange("H6:H26").conditionalFormats.add("containsText", {
  text: "必需", format: { fill: rose, font: { bold: true, color: "#991B1B" } },
});
procurement.getRange("P6:P26").conditionalFormats.add("containsText", {
  text: "已安装", format: { fill: mint, font: { bold: true, color: "#065F46" } },
});
procurement.getRange("P6:P26").conditionalFormats.add("containsText", {
  text: "未采购", format: { fill: gray, font: { color: "#475569" } },
});
procurement.freezePanes.freezeRows(5);
procurement.showGridLines = false;
const widthsA = [["A", 7], ["B", 10], ["C", 12], ["D", 18], ["E", 33], ["F", 8], ["G", 8], ["H", 10], ["I", 13], ["J", 13], ["K", 11], ["L", 13], ["M", 13], ["N", 27], ["O", 34], ["P", 12]];
for (const pair of widthsA) procurement.getRange(pair[0] + ":" + pair[0]).format.columnWidth = pair[1];
procurement.getRange("A6:P26").format.rowHeight = 45;

title(
  parameters,
  "OFDM-ISAC 室内喷淋 Demo - 搭建参数与布置记录",
  "建议采用“50 L 水箱 -> 低压泵 -> 固定花洒 -> 回喷同一水箱”的低成本闭环。主实验中天线、馈线接头、X310 与电源保持干燥；水箱和防溅罩在所有对照状态中位置不变。",
  "H"
);
parameters.mergeCells("A4:H4");
parameters.getRange("A4").values = [[
  "水路简图：水箱（50 L） -> 低压潜水泵或自吸泵（二选一） -> 软管/调节阀 -> 固定花洒 -> 下落水滴幕 -> 回到同一水箱。RF 主视距穿过水滴幕，但不穿过水面；水箱水位保持一致。",
]];
parameters.getRange("A4").format = {
  fill: mint, font: { bold: true, color: text }, wrapText: true,
  verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: border },
};
parameters.getRange("A4").format.rowHeight = 42;
parameters.getRange("A6:H6").values = [[
  "参数", "首版建议值", "可调范围 / 记录方式", "为什么这样设定",
  "每次实验是否固定", "验收 / 备注", "当前值", "状态",
]];
header(parameters.getRange("A6:H6"));
const parameterRows = [
  ["天线间距", "3-5 m 固定视距", "用卷尺记录到 cm", "减小近场耦合，保留室内可搭建性", "是", "天线、喷淋幕、水箱均固定后才采集", "", "待确认"],
  ["喷淋幕位置", "两天线中间附近", "记录距 Tx 与 Rx 的距离", "让水滴处于主传播路径中", "是", "不要让水箱、水面或金属杆进入主瓣", "", "待确认"],
  ["花洒至水面高度", "0.8-1.5 m", "卷尺记录", "形成可见下落水滴并控制飞溅", "是", "高度改变会改变水滴停留时间和空间分布", "", "待确认"],
  ["水箱容量", "50 L", "记录实际初始水位", "满足循环、减少频繁加水", "是", "每轮实验将水位恢复至同一标记", "", "待确认"],
  ["工作频点", "优先 X310 原生 5.8-6 GHz 附近", "记录中心频率、带宽、子载波配置", "不使用变频器下优先提高雨衰敏感度", "是", "实际由 UBX-160 与天线覆盖能力决定", "", "待确认"],
  ["接收增益 / AGC", "固定增益，优先关闭 AGC", "记录模拟增益与数字缩放", "避免增益变化伪造传播衰减", "是", "若无法关闭 AGC，必须逐帧记录并剔除变化段", "", "待确认"],
  ["喷淋等级", "低 / 中 / 高三档", "各档收集 60 s 水量，记 L/min", "第一版只证明可重复等级，不模拟自然雨滴谱", "是", "每档至少重复 3 次，阀门开度拍照", "", "待确认"],
  ["采集时长", "每状态 30-60 s", "记录开始/结束时间", "覆盖稳定段并便于重复", "是", "状态顺序交替，避免温漂混淆", "", "待确认"],
  ["天线与设备干燥", "全程保持干燥", "每组实验前后拍照检查", "隔离水滴路径扰动与湿天线效应", "是", "湿天线仅可作为单独对照实验", "", "待确认"],
  ["水箱与防溅罩", "所有状态均在场", "固定位置、同一水位", "避免对照组几何改变", "是", "干燥基线不允许移走水箱或挡水板", "", "待确认"],
];
parameters.getRange("A7:H16").values = parameterRows;
data(parameters.getRange("A7:H16"));
parameters.getRange("E7:E16").dataValidation = { rule: { type: "list", values: ["是", "否", "按方案"] } };
parameters.getRange("H7:H16").dataValidation = { rule: { type: "list", values: ["待确认", "已确定", "已搭建", "需调整"] } };
parameters.getRange("H7:H16").conditionalFormats.add("containsText", {
  text: "已搭建", format: { fill: mint, font: { bold: true, color: "#065F46" } },
});
parameters.getRange("H7:H16").conditionalFormats.add("containsText", {
  text: "需调整", format: { fill: rose, font: { bold: true, color: "#991B1B" } },
});
parameters.mergeCells("A19:H19");
parameters.getRange("A19").values = [[
  "喷淋等级标定：各档在相同阀门开度 / 泵速下收集 60 s 水量。流量（L/min）= 60 s 内收集水量（L）；此值仅作为受控喷淋强度标签，不等同于自然降雨雨强。",
]];
parameters.getRange("A19").format = {
  fill: amber, font: { bold: true, color: text }, wrapText: true,
  verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: border },
};
parameters.getRange("A19").format.rowHeight = 34;
parameters.getRange("A21:G21").values = [[
  "等级", "阀门 / 泵速记录", "收集时长（s）", "收集水量（L）", "计算流量（L/min）", "重复次数", "备注",
]];
header(parameters.getRange("A21:G21"));
parameters.getRange("A22:G24").values = [
  ["低", "", 60, "", null, 3, ""],
  ["中", "", 60, "", null, 3, ""],
  ["高", "", 60, "", null, 3, ""],
];
parameters.getRange("E22:E24").formulas = [
  ["=IF(OR(C22=\"\",D22=\"\"),\"\",D22/C22*60)"],
  ["=IF(OR(C23=\"\",D23=\"\"),\"\",D23/C23*60)"],
  ["=IF(OR(C24=\"\",D24=\"\"),\"\",D24/C24*60)"],
];
data(parameters.getRange("A22:G24"));
parameters.getRange("C22:C24").format.numberFormat = "#,##0";
parameters.getRange("D22:E24").format.numberFormat = "0.00";
parameters.freezePanes.freezeRows(6);
parameters.showGridLines = false;
const widthsB = [["A", 18], ["B", 26], ["C", 26], ["D", 31], ["E", 15], ["F", 32], ["G", 22], ["H", 13]];
for (const pair of widthsB) parameters.getRange(pair[0] + ":" + pair[0]).format.columnWidth = pair[1];
parameters.getRange("A7:H16").format.rowHeight = 42;

title(
  safety,
  "OFDM-ISAC 室内喷淋 Demo - 安全、对照与验收清单",
  "用于实验前检查、运行中观察和结束后复位。任何涉及设备受潮、增益不可追溯或飞溅进入射频区的项目未通过时，应停止喷淋实验并先整改。",
  "H"
);
safety.getRange("A4:H4").values = [[
  "阶段", "检查项", "检查方法 / 操作", "通过标准", "失败风险", "优先级", "状态", "记录 / 责任人",
]];
header(safety.getRange("A4:H4"));
const safetyRows = [
  ["实验前", "天线与 RF 设备干燥", "检查天线罩、馈线接头、X310、电脑和电源位置", "均在飞溅区外且干燥", "设备损坏；湿天线伪造结果", "高", "未检查", ""],
  ["实验前", "低压供电与漏保", "确认水泵采用 12 V/24 V；交流适配器放高处干燥区", "无裸露交流接头靠近水箱", "触电、短路", "高", "未检查", ""],
  ["实验前", "水路检漏", "不启用 RF 采集时连续循环 10 min", "软管、接头、花洒无渗漏和脱落", "飞溅扩大、流量不稳定", "高", "未检查", ""],
  ["实验前", "水箱与防溅罩固定", "标记水箱位置、水位、挡水板位置", "干燥和喷淋状态均不移动", "几何变化被误判为水滴效应", "高", "未检查", ""],
  ["实验前", "AGC 与增益记录", "关闭 AGC 或记录每帧增益；确认不饱和", "接收增益可追溯且固定", "增益变化伪造成雨衰", "高", "未检查", ""],
  ["实验前", "干燥基线", "水箱、水位、挡板均在场但不喷淋，采集至少 30 s", "基线稳定、无异常跳变", "无法定义喷淋扰动", "高", "未检查", ""],
  ["运行中", "喷头与喷淋幕固定", "检查支架、花洒朝向和阀门开度", "不手持、不扫动，水幕保持在主路径", "标签不重复、遮挡混入", "高", "未检查", ""],
  ["运行中", "喷淋等级标定", "每档收集 60 s 水量并拍摄阀门位置", "低/中/高流量可区分且可重复", "等级标签失真", "中", "未检查", ""],
  ["运行中", "仅泵振动对照", "可选：泵运行但不让水幕进入主路径", "确认泵振动/电磁干扰不主导特征", "将水泵干扰误判为喷淋效应", "中", "未检查", ""],
  ["运行中", "湿地面 / 湿天线对照", "主实验结束后单独进行，不混入主数据", "可量化环境湿润干扰", "结论混淆", "中", "未检查", ""],
  ["结束后", "停泵与断电", "先停止采集，再停泵，断开低压电源", "无带电水路操作", "短路、误操作", "高", "未检查", ""],
  ["结束后", "干燥与清洁", "擦干周边、清洗滤网、排除积水", "天线和接头无水珠", "下次基线受污染", "高", "未检查", ""],
  ["结束后", "数据与元数据归档", "保存干燥/低/中/高标签、流量、增益、频点、时间和照片", "每段数据可追溯", "无法复现实验", "高", "未检查", ""],
];
safety.getRange("A5:H17").values = safetyRows;
data(safety.getRange("A5:H17"));
safety.getRange("F5:F17").dataValidation = { rule: { type: "list", values: ["高", "中", "低"] } };
safety.getRange("G5:G17").dataValidation = { rule: { type: "list", values: ["未检查", "通过", "不通过", "不适用"] } };
safety.getRange("G5:G17").conditionalFormats.add("containsText", {
  text: "通过", format: { fill: mint, font: { bold: true, color: "#065F46" } },
});
safety.getRange("G5:G17").conditionalFormats.add("containsText", {
  text: "不通过", format: { fill: rose, font: { bold: true, color: "#991B1B" } },
});
safety.getRange("F5:F17").conditionalFormats.add("containsText", {
  text: "高", format: { fill: amber, font: { bold: true, color: "#92400E" } },
});
safety.mergeCells("A19:H19");
safety.getRange("A19").values = [[
  "Demo 验收建议：至少三个独立重复中，干燥、低、中、高喷淋状态的接收功率或 CSI 幅度统计应呈现可重复差异；同时报告泵振动、湿地面和湿天线对照，不能将室内喷淋等级表述为自然降雨雨强。",
]];
safety.getRange("A19").format = {
  fill: sky, font: { bold: true, color: text }, wrapText: true,
  verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: border },
};
safety.getRange("A19").format.rowHeight = 40;
safety.freezePanes.freezeRows(4);
safety.showGridLines = false;
const widthsC = [["A", 12], ["B", 21], ["C", 37], ["D", 27], ["E", 29], ["F", 10], ["G", 12], ["H", 20]];
for (const pair of widthsC) safety.getRange(pair[0] + ":" + pair[0]).format.columnWidth = pair[1];
safety.getRange("A5:H17").format.rowHeight = 42;

await fs.mkdir(outputDir, { recursive: true });
const inspection = await workbook.inspect({
  kind: "table",
  range: "器材清单!A1:P12",
  include: "values,formulas",
  tableMaxRows: 12,
  tableMaxCols: 16,
});
console.log(inspection.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "formula error scan",
});
console.log(errors.ndjson);

const previewOne = await workbook.render({ sheetName: "器材清单", autoCrop: "all", scale: 1, format: "png" });
const previewTwo = await workbook.render({ sheetName: "搭建参数", autoCrop: "all", scale: 1, format: "png" });
const previewThree = await workbook.render({ sheetName: "安全与验收", autoCrop: "all", scale: 1, format: "png" });
await fs.writeFile(outputDir + "/器材清单.png", new Uint8Array(await previewOne.arrayBuffer()));
await fs.writeFile(outputDir + "/搭建参数.png", new Uint8Array(await previewTwo.arrayBuffer()));
await fs.writeFile(outputDir + "/安全与验收.png", new Uint8Array(await previewThree.arrayBuffer()));

const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(outputPath);
console.log("Saved " + outputPath);
