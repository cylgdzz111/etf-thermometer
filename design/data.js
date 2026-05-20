// Mock data for ETF温度计
window.MARKETS = [
  { id: 'cn', label: 'A 股', sub: 'CN', count: 218 },
  { id: 'hk', label: '港股', sub: 'HK', count: 64 },
  { id: 'us', label: '美股', sub: 'US', count: 92 },
];

// Helper: temperature color from percentile (0-100)
window.tempColor = function(p) {
  if (p == null) return 'var(--ink-4)';
  if (p < 15) return 'var(--temp-0)';
  if (p < 30) return 'var(--temp-1)';
  if (p < 45) return 'var(--temp-2)';
  if (p < 60) return 'var(--temp-3)';
  if (p < 75) return 'var(--temp-4)';
  if (p < 90) return 'var(--temp-5)';
  return 'var(--temp-6)';
};
window.tempLabel = function(p) {
  if (p == null) return '—';
  if (p < 15) return '极度低估';
  if (p < 30) return '低估';
  if (p < 45) return '偏低';
  if (p < 60) return '正常';
  if (p < 75) return '偏高';
  if (p < 90) return '高估';
  return '极度高估';
};

// Seeded RNG so charts look stable between renders
function mulberry32(a) { return function() { a |= 0; a = a + 0x6D2B79F5 | 0; let t = a; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; } }
window.seedSeries = function(seed, n, base, vol) {
  const r = mulberry32(seed);
  let v = base;
  const out = [];
  for (let i = 0; i < n; i++) {
    v += (r() - 0.5) * vol + Math.sin(i / 9 + seed) * vol * 0.15;
    v = Math.max(base * 0.4, v);
    out.push(v);
  }
  return out;
};

// Market overview series (years on x)
window.MARKET_SERIES = {
  cn: {
    全市场:  seedSeries(11, 200, 28, 1.4),
    沪深300: seedSeries(22, 200, 13, 0.6),
    中证500: seedSeries(33, 200, 26, 1.1),
    创业板:  seedSeries(44, 200, 45, 2.4),
    科创板:  seedSeries(55, 200, 55, 2.8),
  },
  hk: {
    恒生:     seedSeries(61, 200, 11, 0.4),
    恒生科技: seedSeries(62, 200, 22, 1.4),
    国企指数: seedSeries(63, 200, 9, 0.5),
    红筹:     seedSeries(64, 200, 14, 0.7),
  },
  us: {
    标普500:   seedSeries(71, 200, 22, 0.6),
    纳斯达克100: seedSeries(72, 200, 30, 1.0),
    道琼斯:   seedSeries(73, 200, 19, 0.5),
    罗素2000: seedSeries(74, 200, 18, 0.8),
  },
};

// Headline cards
window.MARKET_HEADLINES = {
  cn: [
    { name: '全市场', pe: 58.30, pep: 90.2, pb: 3.41, pbp: 84.5 },
    { name: '主板',   pe: 45.44, pep: 84.3, pb: 2.80, pbp: 79.9 },
    { name: '创业板', pe: 81.79, pep: 90.6, pb: 4.32, pbp: 80.4 },
    { name: '科创板', pe: 94.18, pep: 88.1, pb: 5.06, pbp: 76.0 },
    { name: '北交所', pe: 73.42, pep: 67.9, pb: 3.18, pbp: 54.2 },
  ],
  hk: [
    { name: '恒生指数', pe: 11.42, pep: 38.1, pb: 1.04, pbp: 25.4 },
    { name: '恒生科技', pe: 22.18, pep: 28.7, pb: 2.84, pbp: 31.0 },
    { name: '国企指数', pe: 9.18,  pep: 22.4, pb: 1.02, pbp: 18.2 },
    { name: '红筹指数', pe: 14.34, pep: 44.9, pb: 1.42, pbp: 39.3 },
    { name: '香港中小', pe: 18.21, pep: 52.0, pb: 1.74, pbp: 47.6 },
  ],
  us: [
    { name: '标普500',    pe: 26.30, pep: 88.4, pb: 5.10, pbp: 92.3 },
    { name: '纳斯达克100', pe: 33.88, pep: 84.0, pb: 8.42, pbp: 93.1 },
    { name: '道琼斯',     pe: 22.71, pep: 78.2, pb: 5.84, pbp: 86.5 },
    { name: '罗素2000',   pe: 18.40, pep: 51.1, pb: 2.18, pbp: 38.0 },
    { name: '费城半导体', pe: 38.95, pep: 91.7, pb: 9.18, pbp: 95.6 },
  ],
};

// Sector heatmap data (sector valuation snapshot)
window.SECTORS = {
  cn: [
    { name: '半导体',   pe: 67.4, pct: 92, chg: 2.34 },
    { name: '新能源',   pe: 38.2, pct: 84, chg: 1.42 },
    { name: '医药',     pe: 32.1, pct: 28, chg: -0.62 },
    { name: '银行',     pe: 6.4,  pct: 38, chg: 0.18 },
    { name: '白酒',     pe: 24.3, pct: 12, chg: -1.24 },
    { name: '军工',     pe: 113.5,pct: 96, chg: 1.84 },
    { name: '机器人',   pe: 107.7,pct: 95, chg: 2.42 },
    { name: '券商',     pe: 18.4, pct: 47, chg: 0.94 },
    { name: '地产',     pe: 14.8, pct: 21, chg: -0.34 },
    { name: '基建',     pe: 9.2,  pct: 34, chg: 0.42 },
    { name: '消费',     pe: 22.6, pct: 19, chg: -0.74 },
    { name: '汽车',     pe: 28.1, pct: 62, chg: 1.18 },
    { name: '光伏',     pe: 19.8, pct: 8,  chg: -2.12 },
    { name: '化工',     pe: 16.4, pct: 41, chg: 0.62 },
    { name: '煤炭',     pe: 8.2,  pct: 55, chg: 0.34 },
    { name: '有色',     pe: 17.8, pct: 71, chg: 1.42 },
  ],
  hk: [
    { name: '互联网',   pe: 21.4, pct: 32, chg: 1.18 },
    { name: '生物科技', pe: 24.6, pct: 14, chg: -0.94 },
    { name: '汽车',     pe: 17.8, pct: 48, chg: 0.62 },
    { name: '地产',     pe: 6.4,  pct: 8,  chg: -0.42 },
    { name: '金融',     pe: 8.2,  pct: 28, chg: 0.18 },
    { name: '消费',     pe: 18.4, pct: 24, chg: -0.34 },
    { name: '医药',     pe: 22.1, pct: 22, chg: -1.14 },
    { name: '能源',     pe: 7.2,  pct: 41, chg: 0.74 },
    { name: '电信',     pe: 11.4, pct: 35, chg: 0.22 },
    { name: '公用',     pe: 9.8,  pct: 38, chg: 0.14 },
    { name: '原材料',   pe: 12.6, pct: 52, chg: 0.84 },
    { name: '工业',     pe: 14.2, pct: 44, chg: 0.62 },
    { name: '科技',     pe: 28.4, pct: 38, chg: 1.42 },
    { name: '半导体',   pe: 31.2, pct: 58, chg: 1.92 },
    { name: '物业',     pe: 9.2,  pct: 12, chg: -0.84 },
    { name: '基建',     pe: 8.4,  pct: 31, chg: 0.18 },
  ],
  us: [
    { name: 'AI/半导体',pe: 38.9, pct: 94, chg: 1.82 },
    { name: '云计算',   pe: 41.2, pct: 86, chg: 1.42 },
    { name: '生物医药', pe: 22.4, pct: 54, chg: 0.42 },
    { name: '消费',     pe: 24.6, pct: 72, chg: 0.84 },
    { name: '金融',     pe: 15.2, pct: 68, chg: 0.62 },
    { name: '能源',     pe: 12.1, pct: 32, chg: -0.34 },
    { name: '工业',     pe: 21.4, pct: 74, chg: 0.94 },
    { name: '地产',     pe: 18.2, pct: 41, chg: -0.18 },
    { name: '材料',     pe: 17.4, pct: 58, chg: 0.42 },
    { name: '电信',     pe: 19.8, pct: 64, chg: 0.84 },
    { name: '公用',     pe: 22.1, pct: 71, chg: 0.22 },
    { name: '医疗服务', pe: 26.4, pct: 65, chg: 0.74 },
    { name: '电动车',   pe: 48.2, pct: 79, chg: 2.18 },
    { name: '航空航天', pe: 28.4, pct: 82, chg: 1.42 },
    { name: '消费电子', pe: 31.6, pct: 88, chg: 1.94 },
    { name: '加密相关', pe: 56.4, pct: 91, chg: 3.42 },
  ],
};

// Index list rows. Each: name, code, market, sector, close, chg, w52, peakDist, pe, pep, pb, pbp, fav, spark seed
const _idxBase = [
  // CN
  ['卫星产业',  '931594', 'cn', '军工',     1296.68,  3.36,  95.18, -15.26, 167.87, 94, 6.63, 95],
  ['军工龙头',  '931066', 'cn', '军工',     3604.20,  3.20,  28.38, -22.21, 97.49,  78, 3.72, 71],
  ['高装细分50','931521', 'cn', '军工',     3485.98,  2.85,  38.23, -14.64, 141.98, 88, 5.01, 83],
  ['中证机床',  '931866', 'cn', '装备',     2509.38,  2.42,  94.71,   0.00, 80.36,  91, 6.16, 92],
  ['机器人',    'h30590', 'cn', '机器人',   2108.17,  2.42,  26.78, -26.52, 107.69, 96, 5.41, 99],
  ['空天军工',  '930875', 'cn', '军工',     2616.19,  2.21,  30.94, -32.68, 81.51,  62, 4.21, 58],
  ['中证国防',  '399973', 'cn', '军工',     2003.43,  2.13,  33.08, -38.73, 89.50,  78, 4.18, 59],
  ['中证军工',  '399967', 'cn', '军工',    15058.95,  1.84,  37.39, -31.42, 113.46, 97, 4.79, 80],
  ['沪深300',   '000300', 'cn', '宽基',     3941.22,  0.42,   8.42,  -9.18, 13.21,  48, 1.42, 38],
  ['中证500',   '000905', 'cn', '宽基',     6248.18,  0.94,  14.12, -10.42, 26.44,  61, 1.94, 52],
  ['中证1000',  '000852', 'cn', '宽基',     6694.32,  1.18,  18.21, -12.31, 36.18,  72, 2.18, 64],
  ['创业板指',  '399006', 'cn', '宽基',     2284.18,  1.42,  22.34, -41.22, 41.62,  78, 4.18, 71],
  ['上证50',    '000016', 'cn', '宽基',     2884.21,  0.18,   2.42,  -8.42, 11.42,  41, 1.24, 32],
  ['科创50',    '000688', 'cn', '宽基',     1124.42,  1.84,  24.18, -38.42, 84.21,  82, 4.94, 79],
  ['酒',        '399987', 'cn', '消费',    16842.34, -1.24, -12.42, -45.18, 22.41,  6,  4.84, 8],
  ['医药100',   '000978', 'cn', '医药',     9482.12, -0.42,  -8.42, -38.42, 24.18,  18, 2.42, 14],
  ['中证银行',  '399986', 'cn', '金融',     8421.12,  0.18,  18.42,  -2.42, 6.42,   42, 0.74, 38],
  ['券商',      '399975', 'cn', '金融',     7142.42,  1.18,  24.42, -28.42, 18.42,  48, 1.74, 41],
  ['新能源车',  '399976', 'cn', '新能源',   2841.42,  1.42,  14.42, -32.42, 38.42,  74, 2.84, 68],
  ['光伏产业',  '931151', 'cn', '新能源',   1842.12, -2.12, -42.18, -64.42, 19.81,  8,  1.94, 4],
  // HK
  ['恒生科技',  'HSTECH', 'hk', '科技',     4248.18,  1.42, -12.42, -54.18, 22.18,  29, 2.84, 31],
  ['恒生指数',  'HSI',    'hk', '宽基',    21482.12,  0.84,   8.42, -32.42, 11.42,  38, 1.04, 25],
  ['国企指数',  'HSCEI',  'hk', '宽基',     7642.18,  0.62,  14.42, -42.18, 9.18,   22, 1.02, 18],
  ['恒生互联网','HSIII',  'hk', '互联网',   3142.12,  1.94, -18.42, -68.42, 24.18,  18, 2.21, 19],
  ['恒生医疗',  'HSHCI',  'hk', '医药',     2418.42, -1.42, -28.42, -72.42, 22.41,  14, 1.84, 12],
  // US
  ['标普500',   'SPX',    'us', '宽基',     5842.42,  0.42,  18.42,  -2.42, 26.30,  88, 5.10, 92],
  ['纳斯达克100','NDX',   'us', '科技',    19842.42,  0.84,  28.42,  -3.42, 33.88,  84, 8.42, 93],
  ['道琼斯',    'DJI',    'us', '宽基',    42184.18,  0.18,  14.42,  -1.84, 22.71,  78, 5.84, 87],
  ['罗素2000',  'RUT',    'us', '宽基',     2284.42,  1.18,  22.42, -12.42, 18.40,  51, 2.18, 38],
  ['费城半导体','SOX',    'us', 'AI',       5842.18,  2.42,  48.42,  -8.42, 38.95,  92, 9.18, 96],
  ['标普科技',  'SPNY',   'us', '科技',     8421.42,  1.42,  32.42,  -4.42, 32.18,  86, 8.84, 94],
  ['标普医疗',  'SPHC',   'us', '医药',     3142.18, -0.42,   8.42, -12.42, 22.42,  54, 4.18, 62],
  ['标普能源',  'SPNE',   'us', '能源',      842.42, -0.84,  -4.42, -22.42, 12.18,  32, 2.42, 28],
];

window.INDEX_ROWS = _idxBase.map((r, i) => ({
  name: r[0], code: r[1], market: r[2], sector: r[3],
  close: r[4], chg: r[5], w52: r[6], peakDist: r[7],
  pe: r[8], pep: r[9], pb: r[10], pbp: r[11],
  fav: i < 4 || i === 8 || i === 25,
  sparkSeed: 100 + i,
}));

// Detail-page data
window.DETAIL_INDEX = {
  name: '卫星产业', code: '931594', market: 'cn',
  close: 1296.68, chg: 3.36,
  pe: 167.87, pep: 94.32, pb: 6.63, pbp: 95.18,
  peMin: 85.54, peMax: 182.32, peAvg: 118.03,
  pbMin: 3.52,  pbMax: 8.32,   pbAvg: 5.41,
  totalRet: 76.70, drawdown: -18.91,
  series: seedSeries(931, 180, 100, 1.8),
  peSeries: seedSeries(932, 180, 130, 2.4),
  peDist: seedSeries(933, 40, 30, 12).map(v => Math.max(2, v)),
  pbDist: seedSeries(934, 40, 30, 12).map(v => Math.max(2, v)),
};
