import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ICONS_DIR = path.resolve(__dirname, '..');
if (!process.env.ICON_BUILD_DIR) {
  throw new Error('Set ICON_BUILD_DIR to a writable scratch folder outside assets\\icons (see README.md, "Regenerate").');
}
const SCRATCH_DIR = path.resolve(process.env.ICON_BUILD_DIR);
const requireFromScratch = createRequire(path.join(SCRATCH_DIR, 'package.json'));
const JSZip = requireFromScratch('jszip');
const { PNG } = requireFromScratch('pngjs');
const sharp = requireFromScratch('sharp');

const RETRIEVAL_DATE = '2026-10-19';
const OUTPUT_FILES = [
  'catalog.json',
  'PROVENANCE.md',
  'README.md',
  'contact-sheet.png',
  'STATUS.md',
];
const STATUS_FILE = 'STATUS.md';
const DOWNLOAD_RETRIES = 3;
const DOWNLOAD_TIMEOUT_MS = 45_000;
const PNG_MIN_SIZE = 256;

const PALETTE = {
  ink: '#16202F',
  muted: '#53617A',
  azure: '#0F6CBD',
  azureSoft: '#EAF3FC',
  azureLine: '#BBD7F0',
  amber: '#A64B00',
  amberSoft: '#FFF4E4',
  success: '#1F7A55',
  white: '#FFFFFF',
};

const LUCIDE_COLORS = {
  ink: PALETTE.ink,
  azure: PALETTE.azure,
  amber: PALETTE.amber,
  white: PALETTE.white,
  success: PALETTE.success,
  muted: PALETTE.muted,
};

const LUCIDE_REQUESTS = [
  'database', 'server', 'cloud', 'cpu', 'git-branch', 'git-merge',
  'git-pull-request', 'shield-check', 'lock', 'key-round', 'bell', 'activity',
  'bar-chart-3', 'line-chart', 'table', 'file-text', 'folder', 'layers',
  'workflow', 'rocket', 'refresh-cw', 'repeat', 'play', 'pause', 'check-circle',
  'x-circle', 'alert-triangle', 'clock', 'calendar', 'users', 'user', 'bot',
  'message-square', 'search', 'filter', 'scale', 'gauge', 'flask-conical',
  'brain', 'sparkles', 'network', 'plug', 'box', 'boxes', 'package',
  'container', 'terminal', 'code', 'settings', 'wrench', 'truck', 'factory',
  'building-2', 'map-pin', 'globe', 'eye', 'badge-check', 'flag', 'target',
  'trending-up', 'trending-down', 'arrow-right', 'arrow-down', 'arrow-up-right',
  'zap', 'hard-drive', 'file-json', 'file-spreadsheet', 'split', 'git-compare',
  'history', 'list-checks', 'clipboard-check', 'microscope', 'radar', 'siren',
  'tag', 'link', 'unlink', 'upload', 'download', 'trash-2', 'copy',
  'lightbulb', 'book-open', 'graduation-cap', 'handshake', 'puzzle',
  'shield-alert', 'scroll-text', 'test-tube', 'brackets', 'binary',
];

const LUCIDE_FALLBACKS = {
  'bar-chart-3': ['chart-column'],
  'line-chart': ['chart-line'],
  'check-circle': ['circle-check'],
  'x-circle': ['circle-x'],
  'alert-triangle': ['triangle-alert'],
};

const AZURE_PAGE =
  'https://learn.microsoft.com/en-us/azure/architecture/icons/';
const AZURE_ZIP_URL =
  'https://arch-center.azureedge.net/icons/Azure_Public_Service_Icons_V24.zip';
const FABRIC_PAGE =
  'https://learn.microsoft.com/en-us/fabric/fundamentals/icons';
const FABRIC_PACKAGE_URL =
  'https://www.npmjs.com/package/@fabric-msft/svg-icons';
const ENTRA_PAGE =
  'https://learn.microsoft.com/en-us/entra/architecture/architecture-icons';
const ENTRA_ZIP_URL =
  'https://download.microsoft.com/download/3/1/a/31a56038-856a-4489-88e4-ee5a1c4352be/Microsoft%20Entra%20architecture%20icons%20-%20Oct%202023.zip?wt.mc_id=microsoftentraicons_downloadmicrosoftentraicons_content_cnl_csasci';
const VSCODE_BRAND_PAGE = 'https://code.visualstudio.com/brand';
const VSCODE_ICON_URL = 'https://code.visualstudio.com/assets/branding/code-stable.png';
const OCTICONS_PACKAGE_URL = 'https://www.npmjs.com/package/@primer/octicons';
const OCTICONS_RAW_URL =
  'https://raw.githubusercontent.com/primer/octicons/main/icons/mark-github-16.svg';

const MICROSOFT_ITEMS = [
  {
    name: 'microsoft-fabric',
    label: 'Microsoft Fabric',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'fabric_48_color.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Official Microsoft Fabric npm package asset fabric_48_color.svg.',
  },
  {
    name: 'one-lake',
    label: 'OneLake',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'one_lake_48_color.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Official Microsoft Fabric npm package asset one_lake_48_color.svg.',
  },
  {
    name: 'lakehouse',
    label: 'Lakehouse',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'lakehouse_64_item.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Official Microsoft Fabric npm package asset lakehouse_64_item.svg.',
  },
  {
    name: 'data-warehouse',
    label: 'Data Warehouse',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'data_warehouse_64_item.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Official Microsoft Fabric npm package asset data_warehouse_64_item.svg.',
  },
  {
    name: 'notebook',
    label: 'Notebook',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'notebook_64_item.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Official Microsoft Fabric npm package asset notebook_64_item.svg.',
  },
  {
    name: 'data-pipeline',
    label: 'Data Pipeline',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'pipeline_64_item.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Mapped from “Data Pipeline (Data Factory)” to the current Fabric pipeline item icon pipeline_64_item.svg.',
  },
  {
    name: 'eventhouse',
    label: 'Eventhouse',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'event_house_64_item.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Official Microsoft Fabric npm package asset event_house_64_item.svg.',
  },
  {
    name: 'eventstream',
    label: 'Eventstream',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'eventstream_64_item.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Official Microsoft Fabric npm package asset eventstream_64_item.svg.',
  },
  {
    name: 'data-agent',
    label: 'Data Agent',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'data_agent_64_item.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Official Microsoft Fabric npm package asset data_agent_64_item.svg.',
  },
  {
    name: 'semantic-model',
    label: 'Semantic model',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'semantic_model_64_item.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Official Microsoft Fabric npm package asset semantic_model_64_item.svg.',
  },
  {
    name: 'power-bi',
    label: 'Power BI',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'power_bi_48_color.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Official Microsoft Fabric npm package asset power_bi_48_color.svg.',
  },
  {
    name: 'experiment',
    label: 'Experiment',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'experiments_64_item.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Mapped from the requested “Experiment” concept to the official Fabric experiments item icon experiments_64_item.svg.',
  },
  {
    name: 'ml-model',
    label: 'ML model',
    type: 'fabric-package',
    sourceUrl: FABRIC_PAGE,
    packageUrl: FABRIC_PACKAGE_URL,
    assetPath: 'model_64_item.svg',
    license: 'MIT package; Microsoft Fabric doc permits use in diagrams, training materials, slide decks, and documentation.',
    notes: 'Mapped from the requested “ML model” concept to the official Fabric model item icon model_64_item.svg.',
  },
  {
    name: 'azure-machine-learning',
    label: 'Azure Machine Learning',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/ai + machine learning/038470510-icon-service-Azure-Machine-Learning.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Official Azure architecture icon pack entry 038470510-icon-service-Azure-Machine-Learning.svg.',
  },
  {
    name: 'microsoft-foundry',
    label: 'Microsoft Foundry',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/ai + machine learning/035746832-icon-service-AI-Foundry.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Mapped from “Microsoft Foundry (Azure AI Foundry)” to the current official Azure icon asset 035746832-icon-service-AI-Foundry.svg.',
  },
  {
    name: 'azure-openai-foundry-models',
    label: 'Azure OpenAI / Foundry Models',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/ai + machine learning/038470614-icon-service-Foundry-Models.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Mapped from “Azure OpenAI/Foundry Models” to the current official Foundry Models icon 038470614-icon-service-Foundry-Models.svg.',
  },
  {
    name: 'azure-key-vault',
    label: 'Azure Key Vault',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/security/10245-icon-service-Key-Vaults.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Official Azure architecture icon pack entry 10245-icon-service-Key-Vaults.svg.',
  },
  {
    name: 'azure-container-registry',
    label: 'Azure Container Registry',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/containers/10105-icon-service-Container-Registries.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Official Azure architecture icon pack entry 10105-icon-service-Container-Registries.svg.',
  },
  {
    name: 'azure-storage-account-data-lake',
    label: 'Azure Storage account / Data Lake Storage',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/storage/10086-icon-service-Storage-Accounts.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Used the current Storage Accounts icon; the requested ADLS concept is represented through the storage account surface in the official Azure pack.',
  },
  {
    name: 'application-insights',
    label: 'Application Insights',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/monitor/00012-icon-service-Application-Insights.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Official Azure architecture icon pack entry 00012-icon-service-Application-Insights.svg.',
  },
  {
    name: 'azure-monitor',
    label: 'Azure Monitor',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/monitor/00001-icon-service-Monitor.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Official Azure architecture icon pack entry 00001-icon-service-Monitor.svg.',
  },
  {
    name: 'log-analytics',
    label: 'Log Analytics',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/monitor/00009-icon-service-Log-Analytics-Workspaces.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Official Azure architecture icon pack entry 00009-icon-service-Log-Analytics-Workspaces.svg.',
  },
  {
    name: 'microsoft-entra-id',
    label: 'Microsoft Entra ID',
    type: 'entra-zip',
    sourceUrl: ENTRA_PAGE,
    archiveUrl: ENTRA_ZIP_URL,
    assetPath: 'Microsoft Entra architecture icons - Oct 2023/Microsoft Entra color icons SVG/Microsoft Entra ID color icon.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Official Microsoft Entra architecture icon package color icon.',
  },
  {
    name: 'azure-kubernetes-service',
    label: 'Azure Kubernetes Service',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/containers/10023-icon-service-Kubernetes-Services.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Mapped from AKS to the current official Azure Kubernetes Services icon 10023-icon-service-Kubernetes-Services.svg.',
  },
  {
    name: 'azure-virtual-network',
    label: 'Azure Virtual Network',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/networking/10061-icon-service-Virtual-Networks.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Official Azure architecture icon pack entry 10061-icon-service-Virtual-Networks.svg.',
  },
  {
    name: 'visual-studio-code',
    label: 'Visual Studio Code',
    type: 'direct-png',
    sourceUrl: VSCODE_BRAND_PAGE,
    assetPath: VSCODE_ICON_URL,
    license: 'The VS Code brand page allows use of the stable icon in documentation or tutorials; the icon remains a Microsoft trademark.',
    notes: 'Official stable VS Code icon downloaded from the VS Code brand page.',
  },
  {
    name: 'github',
    label: 'GitHub',
    type: 'octicons-package',
    sourceUrl: OCTICONS_RAW_URL,
    packageUrl: OCTICONS_PACKAGE_URL,
    assetPath: 'mark-github-16.svg',
    license: 'MIT.',
    notes: 'Official GitHub Octicons mark-github asset from @primer/octicons.',
  },
  {
    name: 'azure-devops',
    label: 'Azure DevOps',
    type: 'azure-zip',
    sourceUrl: AZURE_PAGE,
    archiveUrl: AZURE_ZIP_URL,
    assetPath: 'Azure_Public_Service_Icons/Icons/devops/10261-icon-service-Azure-DevOps.svg',
    license: 'Microsoft permits use of these icons in architectural diagrams, training materials, or documentation.',
    notes: 'Official Azure architecture icon pack entry 10261-icon-service-Azure-DevOps.svg.',
  },
];

const TEXT_TILES = [
  'MLflow', 'Spark', 'Delta', 'scikit-learn', 'Python', 'Docker',
  'Git', 'Databricks', 'SQL', 'KQL', 'YAML', 'Bicep', 'OIDC',
];

const MISSING_ITEMS = [
  {
    name: 'activator',
    nearestAlternative: 'No official alternative shipped in the approved Microsoft sources; use a neutral text tile only if a slide must label Activator explicitly.',
    reason: 'No current official Activator icon was found in the Microsoft Fabric Learn download or the official @fabric-msft/svg-icons package.',
  },
  {
    name: 'azure-bicep',
    nearestAlternative: 'No official Microsoft product icon is published in the approved sources; use the neutral bicep text tile when the concept must appear on a slide.',
    reason: 'No official Azure/Bicep product icon was offered in the Azure architecture pack or the other approved Microsoft icon sources checked for this task.',
  },
];

async function main() {
  const versions = await readScratchVersions();
  const catalog = [];
  const provenanceRows = [
    {
      name: 'lucide-static',
      kind: 'lucide',
      sourceUrl: `https://www.npmjs.com/package/lucide-static/v/${versions.lucideVersion}`,
      license: `ISC; lucide-static ${versions.lucideVersion}.`,
      retrievalDate: RETRIEVAL_DATE,
      notes: 'Used for every generic outline icon in the lucide/ and png/<color>/ outputs.',
    },
    {
      name: 'Text tiles',
      kind: 'tiles',
      sourceUrl: 'Generated locally',
      license: 'Generated locally',
      retrievalDate: RETRIEVAL_DATE,
      notes: 'Neutral rounded-square text tiles with text only; no third-party logo artwork is used.',
    },
  ];
  const failures = [];
  const buildRoot = await createBuildRoot();

  await writeStatus({
    phase: 'Preparing build',
    catalog,
    failures,
    details: [
      `Temporary build root: ${toPosixPath(path.relative(ICONS_DIR, buildRoot))}`,
      'Will publish Lucide + catalog first, then Microsoft icons, then tiles/docs.',
    ],
  });

  try {
    const lucideBuild = await buildLucideIcons(buildRoot);
    failures.push(...lucideBuild.missing);
    if (lucideBuild.missing.length === 0) {
      await publishLucideBuild(buildRoot);
      catalog.push(...lucideBuild.entries);
      await writeCatalogJson(catalog, { partial: true, failures });
      await writeStatus({
        phase: 'Lucide published',
        catalog,
        failures,
        details: [`Published ${lucideBuild.entries.length} Lucide SVGs and ${lucideBuild.entries.length * Object.keys(LUCIDE_COLORS).length} color PNGs.`],
      });
    } else {
      await writeStatus({
        phase: 'Lucide failed',
        catalog,
        failures,
        details: ['Lucide outputs were left untouched because one or more requested names failed to build.'],
      });
    }

    const microsoftBuild = await buildMicrosoftIcons(buildRoot, versions.fabricVersion, versions.octiconsVersion);
    provenanceRows.push(...microsoftBuild.provenanceRows);
    failures.push(...microsoftBuild.missing);
    if (microsoftBuild.missing.length === 0) {
      await publishMicrosoftBuild(buildRoot);
      catalog.push(...microsoftBuild.entries);
      await writeCatalogJson(catalog, { partial: true, failures });
      await writeStatus({
        phase: 'Microsoft family published',
        catalog,
        failures,
        details: [`Published ${microsoftBuild.entries.length} official product icons and refreshed catalog.json for slide authors.`],
      });
    } else {
      await writeStatus({
        phase: 'Microsoft family failed',
        catalog,
        failures,
        details: ['Microsoft outputs were left untouched because one or more requested items failed to build.'],
      });
    }

    const tileBuild = await buildTextTiles(buildRoot);
    failures.push(...tileBuild.missing);
    if (tileBuild.missing.length === 0) {
      await publishTilesBuild(buildRoot);
      catalog.push(...tileBuild.entries);
      await writeStatus({
        phase: 'Tiles published',
        catalog,
        failures,
        details: [`Published ${tileBuild.entries.length} neutral text tiles.`],
      });
    } else {
      await writeStatus({
        phase: 'Tiles failed',
        catalog,
        failures,
        details: ['Tile outputs were left untouched because one or more requested tiles failed to build.'],
      });
    }

    await buildContactSheet(catalog);
    await verifyCatalogFilesExist(catalog);
    await verifyPngOutputs(catalog);
    await writeCatalogJson(catalog, { partial: failures.length > 0, failures });
    await writeTextAtomic(path.join(ICONS_DIR, 'PROVENANCE.md'), buildProvenanceMarkdown(provenanceRows, failures));
    await writeTextAtomic(
      path.join(ICONS_DIR, 'README.md'),
      buildReadmeMarkdown({
        lucideVersion: versions.lucideVersion,
        fabricVersion: versions.fabricVersion,
        octiconsVersion: versions.octiconsVersion,
        catalog,
        failures,
      }),
    );
    await writeStatus({
      phase: failures.length === 0 ? 'Build complete' : 'Build completed with failures',
      catalog,
      failures,
      details: failures.length === 0
        ? ['All families published and validated.']
        : ['Some requested names failed; see failures below. Existing published families were not replaced with partial outputs.'],
    });
  } finally {
    await removeIfExists(buildRoot);
  }

  const counts = countCatalogFamilies(catalog);
  const summary = {
    lucide: counts.lucide,
    microsoft: counts.microsoft,
    tiles: counts.tiles,
    failures,
    deliberateAbsences: MISSING_ITEMS.map((item) => item.name),
  };
  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
  if (failures.length > 0) {
    process.exitCode = 1;
  }
}

async function buildLucideIcons(buildRoot) {
  const lucideDir = path.join(SCRATCH_DIR, 'node_modules', 'lucide-static', 'icons');
  const entries = [];
  const missing = [];
  const familyRoot = path.join(buildRoot, 'lucide');
  const pngRoot = path.join(buildRoot, 'png');
  await ensureDir(familyRoot);
  for (const colorName of Object.keys(LUCIDE_COLORS)) {
    await ensureDir(path.join(pngRoot, colorName));
  }
  for (const requestedName of LUCIDE_REQUESTS) {
    try {
      const resolvedName = await resolveLucideName(lucideDir, requestedName);
      const sourcePath = path.join(lucideDir, `${resolvedName}.svg`);
      const sourceSvg = await fs.readFile(sourcePath, 'utf8');
      const normalizedSvg = normalizeLucideSvg(sourceSvg);
      const relativeSvgPath = path.join('lucide', `${requestedName}.svg`);
      await writeText(path.join(buildRoot, relativeSvgPath), normalizedSvg);

      const pngPaths = {};
      for (const [colorName, colorHex] of Object.entries(LUCIDE_COLORS)) {
        const pngRelativePath = path.join('png', colorName, `${requestedName}.png`);
        const pngAbsolutePath = path.join(buildRoot, pngRelativePath);
        const renderSvg = buildLucideRenderSvg(normalizedSvg, colorHex);
        await renderSvgToPng(renderSvg, pngAbsolutePath);
        pngPaths[colorName] = toPosixPath(pngRelativePath);
      }

      const notes = resolvedName === requestedName
        ? ''
        : `Requested ${requestedName}; used Lucide ${resolvedName}.`;
      entries.push(makeCatalogEntry({
        name: requestedName,
        family: 'lucide',
        kind: 'lucide',
        svg: relativeSvgPath,
        png: pngPaths,
        availableColors: Object.keys(LUCIDE_COLORS),
        sourceUrl: `https://lucide.dev/icons/${resolvedName}`,
        license: 'ISC',
        notes,
      }));
      process.stdout.write(`[lucide] ${entries.length}/${LUCIDE_REQUESTS.length} ${requestedName}\n`);
    } catch (error) {
      missing.push({
        family: 'lucide',
        name: requestedName,
        reason: error.message,
      });
      process.stderr.write(`[lucide] failed: ${requestedName}: ${error.message}\n`);
    }
  }
  return { entries, missing };
}

async function resolveLucideName(lucideDir, requestedName) {
  const candidates = [requestedName, ...(LUCIDE_FALLBACKS[requestedName] || [])];
  for (const candidate of candidates) {
    try {
      await fs.access(path.join(lucideDir, `${candidate}.svg`));
      return candidate;
    } catch {
      // Continue to next candidate.
    }
  }
  throw new Error(`No Lucide icon found for ${requestedName}. Checked: ${candidates.join(', ')}`);
}

function normalizeLucideSvg(svgText) {
  return svgText
    .replace(/\r\n/g, '\n')
    .replace(/stroke-width="[^"]*"/g, 'stroke-width="1.75"')
    .replace(/<svg\b([^>]*?)>/, (match, attrs) => {
      const nextAttrs = attrs
        .replace(/\s(width|height)="[^"]*"/g, '')
        .replace(/\s(class|data-name)="[^"]*"/g, '');
      return `<svg xmlns="http://www.w3.org/2000/svg"${nextAttrs}>`;
    });
}

function buildLucideRenderSvg(sourceSvg, strokeColor) {
  const innerSvg = extractSvgInner(sourceSvg);
  return [
    '<svg xmlns="http://www.w3.org/2000/svg" width="384" height="384" viewBox="0 0 384 384">',
    '<style>*{vector-effect:non-scaling-stroke}</style>',
    `<g fill="none" stroke="${strokeColor}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" transform="translate(24 24) scale(14)">`,
    innerSvg,
    '</g>',
    '</svg>',
  ].join('');
}

async function buildMicrosoftIcons(buildRoot, fabricVersion, octiconsVersion) {
  const downloadsDir = path.join(SCRATCH_DIR, 'downloads');
  await ensureDir(downloadsDir);
  const azureZip = await loadZipCached(downloadsDir, 'azure-icons-v24.zip', AZURE_ZIP_URL);
  const entraZip = await loadZipCached(downloadsDir, 'entra-icons-oct-2023.zip', ENTRA_ZIP_URL);

  const entries = [];
  const provenanceRows = [];
  const missing = [];
  await ensureDir(path.join(buildRoot, 'microsoft', 'svg'));
  await ensureDir(path.join(buildRoot, 'microsoft', 'png'));

  for (const item of MICROSOFT_ITEMS) {
    try {
      let svgText = null;
      let pngBuffer = null;
      let relativeSvgPath = null;
      const relativePngPath = path.join('microsoft', 'png', `${item.name}.png`);
      const absolutePngPath = path.join(buildRoot, relativePngPath);

      if (item.type === 'fabric-package') {
        svgText = await fs.readFile(
          path.join(SCRATCH_DIR, 'node_modules', '@fabric-msft', 'svg-icons', 'svg', item.assetPath),
          'utf8',
        );
        relativeSvgPath = path.join('microsoft', 'svg', `${item.name}.svg`);
        await writeText(path.join(buildRoot, relativeSvgPath), svgText);
        await renderSvgToPng(wrapSvgInSquare(svgText, 512, 40), absolutePngPath);
        provenanceRows.push({
          name: item.label,
          kind: 'microsoft',
          sourceUrl: item.packageUrl || item.sourceUrl,
          license: `${item.license} Package version ${fabricVersion}.`,
          retrievalDate: RETRIEVAL_DATE,
          notes: `${item.notes} Source page: ${item.sourceUrl}`,
        });
      } else if (item.type === 'azure-zip') {
        svgText = await readZipEntryText(azureZip, item.assetPath);
        relativeSvgPath = path.join('microsoft', 'svg', `${item.name}.svg`);
        await writeText(path.join(buildRoot, relativeSvgPath), svgText);
        await renderSvgToPng(wrapSvgInSquare(svgText, 512, 40), absolutePngPath);
        provenanceRows.push({
          name: item.label,
          kind: 'microsoft',
          sourceUrl: item.sourceUrl,
          license: item.license,
          retrievalDate: RETRIEVAL_DATE,
          notes: `${item.notes} Archive URL: ${item.archiveUrl}`,
        });
      } else if (item.type === 'entra-zip') {
        svgText = await readZipEntryText(entraZip, item.assetPath);
        relativeSvgPath = path.join('microsoft', 'svg', `${item.name}.svg`);
        await writeText(path.join(buildRoot, relativeSvgPath), svgText);
        await renderSvgToPng(wrapSvgInSquare(svgText, 512, 40), absolutePngPath);
        provenanceRows.push({
          name: item.label,
          kind: 'microsoft',
          sourceUrl: item.sourceUrl,
          license: item.license,
          retrievalDate: RETRIEVAL_DATE,
          notes: `${item.notes} Archive URL: ${item.archiveUrl}`,
        });
      } else if (item.type === 'direct-png') {
        pngBuffer = await downloadBinaryCached(downloadsDir, 'visual-studio-code.png', item.assetPath);
        await renderPngToPngSquare(pngBuffer, absolutePngPath, 512, 32);
        provenanceRows.push({
          name: item.label,
          kind: 'microsoft',
          sourceUrl: item.sourceUrl,
          license: item.license,
          retrievalDate: RETRIEVAL_DATE,
          notes: item.notes,
        });
      } else if (item.type === 'octicons-package') {
        svgText = await fs.readFile(
          path.join(SCRATCH_DIR, 'node_modules', '@primer', 'octicons', 'build', 'svg', item.assetPath),
          'utf8',
        );
        relativeSvgPath = path.join('microsoft', 'svg', `${item.name}.svg`);
        await writeText(path.join(buildRoot, relativeSvgPath), svgText);
        await renderSvgToPng(wrapSvgInSquare(svgText, 512, 64), absolutePngPath);
        provenanceRows.push({
          name: item.label,
          kind: 'microsoft',
          sourceUrl: item.sourceUrl,
          license: `${item.license} Package version ${octiconsVersion}.`,
          retrievalDate: RETRIEVAL_DATE,
          notes: `${item.notes} Package URL: ${item.packageUrl}`,
        });
      } else {
        throw new Error(`Unsupported Microsoft icon source type: ${item.type}`);
      }

      entries.push(makeCatalogEntry({
        name: item.name,
        family: 'microsoft',
        kind: 'microsoft',
        svg: relativeSvgPath,
        png: relativePngPath,
        availableColors: [],
        sourceUrl: item.sourceUrl,
        license: item.license,
        notes: item.notes,
      }));
      process.stdout.write(`[microsoft] ${entries.length}/${MICROSOFT_ITEMS.length} ${item.name}\n`);
    } catch (error) {
      missing.push({
        family: 'microsoft',
        name: item.name,
        reason: error.message,
      });
      process.stderr.write(`[microsoft] failed: ${item.name}: ${error.message}\n`);
    }
  }

  return { entries, provenanceRows, missing };
}

async function buildTextTiles(buildRoot) {
  const entries = [];
  const missing = [];
  await ensureDir(path.join(buildRoot, 'tiles'));
  for (const tileName of TEXT_TILES) {
    try {
      const safeName = slugify(tileName);
      const relativePngPath = path.join('tiles', `${safeName}.png`);
      const absolutePngPath = path.join(buildRoot, relativePngPath);
      const tileSvg = buildTileSvg(tileName);
      await renderSvgToPng(tileSvg, absolutePngPath);
      entries.push(makeCatalogEntry({
        name: safeName,
        family: 'tiles',
        kind: 'tile',
        svg: null,
        png: relativePngPath,
        availableColors: [],
        sourceUrl: null,
        license: 'Generated locally',
        notes: `Neutral text tile for ${tileName}; no third-party logo used.`,
      }));
      process.stdout.write(`[tiles] ${entries.length}/${TEXT_TILES.length} ${safeName}\n`);
    } catch (error) {
      missing.push({
        family: 'tiles',
        name: slugify(tileName),
        reason: error.message,
      });
      process.stderr.write(`[tiles] failed: ${tileName}: ${error.message}\n`);
    }
  }
  return { entries, missing };
}

function buildTileSvg(label) {
  const lines = wrapWords(label, 12);
  const fontSize = lines.length > 1 ? 78 : label.length > 10 ? 74 : 88;
  const lineHeight = Math.round(fontSize * 1.1);
  const centerY = 256 - ((lines.length - 1) * lineHeight) / 2;
  const tspans = lines
    .map((line, index) => {
      const dy = index === 0 ? 0 : lineHeight;
      const y = index === 0 ? centerY : null;
      return `<tspan x="256"${y === null ? ` dy="${dy}"` : ` y="${y}"`}>${escapeXml(line)}</tspan>`;
    })
    .join('');

  return [
    '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">',
    `<rect x="18" y="18" width="476" height="476" rx="36" fill="${PALETTE.azureSoft}" stroke="${PALETTE.azureLine}" stroke-width="6"/>`,
    `<text x="256" text-anchor="middle" font-family="Segoe UI, Trebuchet MS, Arial, sans-serif" font-weight="700" font-size="${fontSize}" fill="${PALETTE.ink}">`,
    tspans,
    '</text>',
    '</svg>',
  ].join('');
}

async function buildContactSheet(catalog) {
  const representativeItems = catalog.map((entry) => ({
    label: humanLabel(entry.name),
    pngPath: path.join(ICONS_DIR, getRepresentativePngPath(entry)),
  }));
  const columns = 8;
  const cellWidth = 220;
  const cellHeight = 200;
  const padding = 24;
  const rows = Math.ceil(representativeItems.length / columns);
  const width = columns * cellWidth + padding * 2;
  const height = rows * cellHeight + padding * 2 + 30;

  const composites = [];
  const textParts = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
    `<text x="${padding}" y="28" font-family="Segoe UI, Trebuchet MS, Arial, sans-serif" font-size="20" font-weight="700" fill="${PALETTE.ink}">Icon contact sheet</text>`,
  ];

  for (const [index, item] of representativeItems.entries()) {
    const col = index % columns;
    const row = Math.floor(index / columns);
    const x = padding + col * cellWidth;
    const y = padding + 30 + row * cellHeight;
    const imageX = x + 46;
    const imageY = y + 8;
    const imageSize = 110;
    const lines = wrapWords(item.label, 16).slice(0, 3);
    composites.push({
      input: await sharp(await fs.readFile(item.pngPath))
        .resize({ width: imageSize, height: imageSize, fit: 'contain' })
        .png()
        .toBuffer(),
      left: imageX,
      top: imageY,
    });
    textParts.push(`<text x="${x + cellWidth / 2}" y="${y + 138}" text-anchor="middle" font-family="Segoe UI, Trebuchet MS, Arial, sans-serif" font-size="14" fill="${PALETTE.ink}">`);
    for (const [lineIndex, line] of lines.entries()) {
      const dy = lineIndex === 0 ? 0 : 18;
      const yLine = lineIndex === 0 ? y + 138 : null;
      textParts.push(`<tspan x="${x + cellWidth / 2}"${yLine === null ? ` dy="${dy}"` : ` y="${yLine}"`}>${escapeXml(line)}</tspan>`);
    }
    textParts.push('</text>');
  }

  textParts.push('</svg>');
  await sharp({
    create: {
      width,
      height,
      channels: 4,
      background: PALETTE.white,
    },
  })
    .composite([
      ...composites,
      {
        input: Buffer.from(textParts.join('')),
        left: 0,
        top: 0,
      },
    ])
    .png()
    .toFile(path.join(ICONS_DIR, 'contact-sheet.png'));
}

async function verifyCatalogFilesExist(catalog) {
  for (const entry of catalog) {
    if (entry.files.svg) {
      await fs.access(path.join(ICONS_DIR, entry.files.svg));
    }
    if (entry.kind === 'lucide') {
      for (const pngPath of Object.values(entry.files.png)) {
        await fs.access(path.join(ICONS_DIR, pngPath));
      }
    } else {
      await fs.access(path.join(ICONS_DIR, entry.files.png));
    }
  }
}

async function verifyPngOutputs(catalog) {
  const pngPaths = [];
  for (const entry of catalog) {
    if (entry.kind === 'lucide') {
      pngPaths.push(...Object.values(entry.files.png));
    } else {
      pngPaths.push(entry.files.png);
    }
  }
  pngPaths.push('contact-sheet.png');

  for (const relativePath of pngPaths) {
    const buffer = await fs.readFile(path.join(ICONS_DIR, relativePath));
    const png = PNG.sync.read(buffer);
    if (png.width < PNG_MIN_SIZE || png.height < PNG_MIN_SIZE) {
      throw new Error(`PNG too small (${png.width}x${png.height}): ${relativePath}`);
    }
    if (!hasVisiblePixels(png)) {
      throw new Error(`Blank PNG detected: ${relativePath}`);
    }
  }
}

function hasVisiblePixels(png) {
  for (let i = 3; i < png.data.length; i += 4) {
    if (png.data[i] > 0) {
      return true;
    }
  }
  return false;
}

function buildProvenanceMarkdown(rows, failures) {
  const lines = [
    '# Provenance',
    '',
    '| Name | Kind | Source URL | Licence / terms | Retrieval date | Notes |',
    '| --- | --- | --- | --- | --- | --- |',
  ];
  for (const row of rows) {
    lines.push(
      `| ${escapePipe(row.name)} | ${escapePipe(row.kind)} | ${escapePipe(row.sourceUrl)} | ${escapePipe(row.license)} | ${escapePipe(row.retrievalDate)} | ${escapePipe(row.notes)} |`,
    );
  }
  lines.push(
    '',
    '## Official names that remain deliberately absent',
    '',
  );
  for (const item of MISSING_ITEMS) {
    lines.push(`- \`${item.name}\`: ${item.reason} Nearest alternative: ${item.nearestAlternative}`);
  }
  if (failures.length > 0) {
    lines.push(
      '',
      '## Build failures',
      '',
    );
    for (const failure of failures) {
      lines.push(`- \`${failure.family}/${failure.name}\`: ${failure.reason}`);
    }
  }
  lines.push('');
  return `${lines.join('\n')}\n`;
}

function buildReadmeMarkdown({ lucideVersion, fabricVersion, octiconsVersion, catalog, failures }) {
  const counts = countCatalogFamilies(catalog);
  const lines = [
    '# Icon build',
    '',
    'Generated icon set for the ML platforms deck.',
    '',
    '## Regenerate',
    '',
    '1. Pick a scratch folder outside `assets\\icons`, set the `ICON_BUILD_DIR` environment variable to it, and install the dependencies there if they are missing:',
    '   - `npm install --prefix "%ICON_BUILD_DIR%" sharp lucide-static @fabric-msft/svg-icons @primer/octicons jszip pngjs --no-audit --no-fund`',
    '2. From this folder, run:',
    '   - `node scripts\\build_icons.mjs`',
    '',
    'The build is family-safe: it renders into a temporary folder under `assets\\icons`, publishes each family only after that family is complete, retries downloads, and leaves previously published families untouched if a later family fails.',
    '',
    'The script writes:',
    '',
    '- `lucide\\*.svg` and `png\\<color>\\*.png`',
    '- `microsoft\\svg\\*.svg` and `microsoft\\png\\*.png`',
    '- `tiles\\*.png`',
    '- `catalog.json`, `PROVENANCE.md`, `README.md`, `STATUS.md`, `contact-sheet.png`',
    '',
    '## Naming rules',
    '',
    '- File names are stable slugs used directly by slide authors (`add_icon(..., "name")`).',
    '- Lucide compatibility aliases keep the requested old deck names even when Lucide renamed the upstream glyph.',
    '- Microsoft assets stay colourless and unmodified; only placement/scaling changes when rasterising PNGs.',
    '- Text tiles are neutral labels, not vendor logos.',
    '',
    '## How the deck loads icons',
    '',
    '- `deck_core.py::icon_file()` scans every PNG under `assets\\icons`.',
    '- A parent folder named `amber`, `azure`, `ink`, `muted`, `success`, or `white` marks a Lucide colour variant.',
    '- Lookup order is `(name, color)`, `(name, none)`, `(name, azure)`, then any remaining match.',
    '',
    '## Sources and package versions',
    '',
    `- Lucide generic icons: \`lucide-static ${lucideVersion}\` (ISC)`,
    `- Microsoft Fabric icons: \`@fabric-msft/svg-icons ${fabricVersion}\` (MIT package; Microsoft Learn usage terms also reviewed)`,
    `- GitHub mark: \`@primer/octicons ${octiconsVersion}\` (MIT)`,
    `- Azure, Entra, VS Code: official Microsoft downloads / brand pages referenced in \`PROVENANCE.md\``,
    '',
    '## Missing items',
    '',
  ];
  for (const item of MISSING_ITEMS) {
    lines.push(`- \`${item.name}\`: ${item.reason} Nearest alternative: ${item.nearestAlternative}`);
  }
  lines.push(
    '',
    '## Catalog counts',
    '',
    `- Lucide: ${counts.lucide}`,
    `- Microsoft / official vendor: ${counts.microsoft}`,
    `- Text tiles: ${counts.tiles}`,
    '',
  );
  if (failures.length > 0) {
    lines.push(
      '## Build failures',
      '',
    );
    for (const failure of failures) {
      lines.push(`- \`${failure.family}/${failure.name}\`: ${failure.reason}`);
    }
    lines.push('');
  }
  return `${lines.join('\n')}\n`;
}

async function readScratchVersions() {
  const lucideVersion = JSON.parse(
    await fs.readFile(
      path.join(SCRATCH_DIR, 'node_modules', 'lucide-static', 'package.json'),
      'utf8',
    ),
  ).version;
  const fabricVersion = JSON.parse(
    await fs.readFile(
      path.join(SCRATCH_DIR, 'node_modules', '@fabric-msft', 'svg-icons', 'package.json'),
      'utf8',
    ),
  ).version;
  const octiconsVersion = JSON.parse(
    await fs.readFile(
      path.join(SCRATCH_DIR, 'node_modules', '@primer', 'octicons', 'package.json'),
      'utf8',
    ),
  ).version;
  return { lucideVersion, fabricVersion, octiconsVersion };
}

async function createBuildRoot() {
  const stamp = new Date().toISOString().replace(/[:.]/g, '').replace('T', '-').replace('Z', '');
  const buildRoot = path.join(ICONS_DIR, `.build-${stamp}-${process.pid}`);
  await removeIfExists(buildRoot);
  await ensureDir(buildRoot);
  return buildRoot;
}

async function publishLucideBuild(buildRoot) {
  await swapDirectory(path.join(buildRoot, 'lucide'), path.join(ICONS_DIR, 'lucide'));
  await swapDirectory(path.join(buildRoot, 'png'), path.join(ICONS_DIR, 'png'));
}

async function publishMicrosoftBuild(buildRoot) {
  await swapDirectory(path.join(buildRoot, 'microsoft'), path.join(ICONS_DIR, 'microsoft'));
}

async function publishTilesBuild(buildRoot) {
  await swapDirectory(path.join(buildRoot, 'tiles'), path.join(ICONS_DIR, 'tiles'));
}

async function swapDirectory(sourceDir, targetDir) {
  const backupDir = `${targetDir}.bak`;
  await ensureDir(path.dirname(targetDir));
  await removeIfExists(backupDir);
  const targetExists = await pathExists(targetDir);
  if (targetExists) {
    await fs.rename(targetDir, backupDir);
  }
  try {
    await fs.rename(sourceDir, targetDir);
    await removeIfExists(backupDir);
  } catch (error) {
    await removeIfExists(targetDir);
    if (await pathExists(backupDir)) {
      await fs.rename(backupDir, targetDir);
    }
    throw error;
  }
}

async function loadZipCached(downloadsDir, fileName, url) {
  const buffer = await downloadBinaryCached(downloadsDir, fileName, url);
  return JSZip.loadAsync(buffer);
}

async function downloadBinaryCached(downloadsDir, fileName, url) {
  const filePath = path.join(downloadsDir, fileName);
  try {
    return await fs.readFile(filePath);
  } catch {
    let lastError = null;
    for (let attempt = 1; attempt <= DOWNLOAD_RETRIES; attempt += 1) {
      try {
        const response = await fetch(url, {
          signal: AbortSignal.timeout(DOWNLOAD_TIMEOUT_MS),
          headers: { 'user-agent': 'ml-workshop-icon-builder/1.0' },
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status} ${response.statusText}`);
        }
        const arrayBuffer = await response.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);
        await fs.writeFile(filePath, buffer);
        return buffer;
      } catch (error) {
        lastError = error;
        await removeIfExists(filePath);
        if (attempt < DOWNLOAD_RETRIES) {
          process.stderr.write(`[download] retry ${attempt}/${DOWNLOAD_RETRIES - 1} for ${fileName}: ${error.message}\n`);
          await wait(1_000 * attempt);
        }
      }
    }
    throw new Error(`Failed to download ${url} after ${DOWNLOAD_RETRIES} attempts: ${lastError.message}`);
  }
}

async function readZipEntryText(zip, entryPath) {
  const file = zip.file(entryPath);
  if (!file) {
    throw new Error(`Zip entry not found: ${entryPath}`);
  }
  return file.async('string');
}

function wrapSvgInSquare(svgText, size, padding) {
  const { viewBox, width, height, inner } = parseSvg(svgText);
  const innerMax = size - padding * 2;
  const scale = Math.min(innerMax / width, innerMax / height);
  const renderWidth = width * scale;
  const renderHeight = height * scale;
  const x = (size - renderWidth) / 2;
  const y = (size - renderHeight) / 2;
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">`,
    `<svg x="${x}" y="${y}" width="${renderWidth}" height="${renderHeight}" viewBox="${viewBox}">`,
    inner,
    '</svg>',
    '</svg>',
  ].join('');
}

function wrapPngInSquare(pngBuffer, size, padding) {
  const png = PNG.sync.read(pngBuffer);
  const innerMax = size - padding * 2;
  const scale = Math.min(innerMax / png.width, innerMax / png.height);
  const renderWidth = png.width * scale;
  const renderHeight = png.height * scale;
  const x = (size - renderWidth) / 2;
  const y = (size - renderHeight) / 2;
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">`,
    `<image href="data:image/png;base64,${pngBuffer.toString('base64')}" x="${x}" y="${y}" width="${renderWidth}" height="${renderHeight}"/>`,
    '</svg>',
  ].join('');
}

function parseSvg(svgText) {
  const viewBoxMatch = svgText.match(/viewBox="([^"]+)"/i);
  if (viewBoxMatch) {
    const [minX, minY, width, height] = viewBoxMatch[1].trim().split(/\s+/).map(Number);
    if (![minX, minY, width, height].every(Number.isFinite)) {
      throw new Error(`Unable to parse viewBox: ${viewBoxMatch[1]}`);
    }
    return {
      viewBox: `${minX} ${minY} ${width} ${height}`,
      width,
      height,
      inner: extractSvgInner(svgText),
    };
  }
  const widthMatch = svgText.match(/\bwidth="([^"]+)"/i);
  const heightMatch = svgText.match(/\bheight="([^"]+)"/i);
  if (!widthMatch || !heightMatch) {
    throw new Error('SVG is missing a viewBox and explicit width/height.');
  }
  const width = parseFloat(widthMatch[1].replace(/px$/i, ''));
  const height = parseFloat(heightMatch[1].replace(/px$/i, ''));
  if (![width, height].every(Number.isFinite)) {
    throw new Error(`Unable to parse SVG size: width=${widthMatch[1]} height=${heightMatch[1]}`);
  }
  return {
    viewBox: `0 0 ${width} ${height}`,
    width,
    height,
    inner: extractSvgInner(svgText),
  };
}

function extractSvgInner(svgText) {
  return svgText
    .replace(/\r\n/g, '\n')
    .replace(/^[\s\S]*?<svg\b[^>]*>/i, '')
    .replace(/<\/svg>[\s\S]*$/i, '');
}

async function renderSvgToPng(svgText, outputPath) {
  await sharp(Buffer.from(svgText))
    .png()
    .toFile(outputPath);
}

async function renderPngToPngSquare(pngBuffer, outputPath, size, padding) {
  const source = sharp(pngBuffer);
  const metadata = await source.metadata();
  if (!metadata.width || !metadata.height) {
    throw new Error('Unable to read PNG dimensions.');
  }
  const innerMax = size - padding * 2;
  const scale = Math.min(innerMax / metadata.width, innerMax / metadata.height);
  const renderWidth = Math.max(1, Math.round(metadata.width * scale));
  const renderHeight = Math.max(1, Math.round(metadata.height * scale));
  const resized = await source
    .resize({ width: renderWidth, height: renderHeight, fit: 'contain' })
    .png()
    .toBuffer();
  const left = Math.round((size - renderWidth) / 2);
  const top = Math.round((size - renderHeight) / 2);
  await sharp({
    create: {
      width: size,
      height: size,
      channels: 4,
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    },
  })
    .composite([{ input: resized, left, top }])
    .png()
    .toFile(outputPath);
}

async function ensureDir(dirPath) {
  await fs.mkdir(dirPath, { recursive: true });
}

async function removeIfExists(targetPath) {
  await fs.rm(targetPath, { force: true, recursive: true });
}

async function writeText(filePath, content) {
  const normalized = content.replace(/\r\n/g, '\n');
  await fs.writeFile(filePath, normalized, 'utf8');
}

async function writeTextAtomic(filePath, content) {
  const tempPath = `${filePath}.tmp`;
  await writeText(tempPath, content);
  await removeIfExists(filePath);
  await fs.rename(tempPath, filePath);
}

async function writeCatalogJson(catalog, { partial, failures }) {
  const payload = {
    generatedAt: new Date().toISOString(),
    partial,
    counts: {
      planned: {
        lucide: LUCIDE_REQUESTS.length,
        microsoft: MICROSOFT_ITEMS.length,
        tiles: TEXT_TILES.length,
      },
      ready: countCatalogFamilies(catalog),
    },
    deliberateAbsences: MISSING_ITEMS,
    failures,
    icons: catalog,
  };
  await writeTextAtomic(
    path.join(ICONS_DIR, 'catalog.json'),
    `${JSON.stringify(payload, null, 2)}\n`,
  );
}

async function writeStatus({ phase, catalog, failures, details }) {
  const counts = countCatalogFamilies(catalog);
  const lines = [
    '# Icon library status',
    '',
    `- Phase: ${phase}`,
    `- Updated: ${new Date().toISOString()}`,
    `- Lucide ready: ${counts.lucide}/${LUCIDE_REQUESTS.length}`,
    `- Microsoft ready: ${counts.microsoft}/${MICROSOFT_ITEMS.length}`,
    `- Tiles ready: ${counts.tiles}/${TEXT_TILES.length}`,
    '',
    '## Notes',
    '',
  ];
  for (const detail of details) {
    lines.push(`- ${detail}`);
  }
  lines.push(
    '',
    '## Deliberate official absences',
    '',
  );
  for (const item of MISSING_ITEMS) {
    lines.push(`- \`${item.name}\`: ${item.reason}`);
  }
  if (failures.length > 0) {
    lines.push(
      '',
      '## Failures',
      '',
    );
    for (const failure of failures) {
      lines.push(`- \`${failure.family}/${failure.name}\`: ${failure.reason}`);
    }
  }
  lines.push('');
  await writeTextAtomic(path.join(ICONS_DIR, STATUS_FILE), `${lines.join('\n')}\n`);
}

function makeCatalogEntry({ name, family, kind, svg, png, availableColors, sourceUrl, license, notes }) {
  const svgPath = svg ? toPosixPath(svg) : null;
  const pngPath = typeof png === 'string'
    ? toPosixPath(png)
    : Object.fromEntries(Object.entries(png).map(([key, value]) => [key, toPosixPath(value)]));
  return {
    name,
    family,
    kind,
    files: {
      svg: svgPath,
      png: pngPath,
    },
    availableColors,
    source: {
      url: sourceUrl,
      license,
      notes,
    },
    svg: svgPath,
    png: pngPath,
    license,
    notes,
  };
}

function countCatalogFamilies(catalog) {
  return {
    lucide: catalog.filter((entry) => entry.family === 'lucide').length,
    microsoft: catalog.filter((entry) => entry.family === 'microsoft').length,
    tiles: catalog.filter((entry) => entry.family === 'tiles').length,
  };
}

function getRepresentativePngPath(entry) {
  return entry.kind === 'lucide' ? entry.files.png.ink : entry.files.png;
}

async function pathExists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function wait(ms) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

function wrapWords(text, maxChars) {
  if (text.length <= maxChars) {
    return [text];
  }
  const tokens = text
    .replace(/-/g, '- ')
    .split(/\s+/)
    .filter(Boolean);
  const lines = [];
  let current = '';
  for (const token of tokens) {
    const cleanToken = token.endsWith('-') ? token.slice(0, -1) : token;
    const candidate = current ? `${current} ${cleanToken}` : cleanToken;
    if (candidate.length <= maxChars || current.length === 0) {
      current = candidate;
    } else {
      lines.push(current);
      current = cleanToken;
    }
  }
  if (current) {
    lines.push(current);
  }
  return lines;
}

function humanLabel(slug) {
  return slug
    .replace(/-/g, ' ')
    .replace(/\bml\b/g, 'ML')
    .replace(/\bid\b/g, 'ID')
    .replace(/\boidc\b/g, 'OIDC')
    .replace(/\bkql\b/g, 'KQL')
    .replace(/\bsql\b/g, 'SQL')
    .replace(/\byaml\b/g, 'YAML')
    .replace(/\bgithub\b/g, 'GitHub')
    .replace(/\bvscode\b/g, 'VS Code')
    .replace(/\b[a-z]/g, (char) => char.toUpperCase());
}

function slugify(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

function escapeXml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function escapePipe(text) {
  return String(text).replace(/\|/g, '\\|');
}

function toPosixPath(filePath) {
  return filePath.split(path.sep).join('/');
}

function toWindowsPath(filePath) {
  return filePath.split('/').join('\\');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
