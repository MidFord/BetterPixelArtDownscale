export class DownscaleOptions {
  constructor(options = {}) {
    this.alphaThreshold = options.alphaThreshold ?? options.alpha_threshold ?? 0.50;
    this.sourceAlphaThreshold = options.sourceAlphaThreshold ?? options.source_alpha_threshold ?? (1.0 / 255.0);
    this.preserveThinFeatures = options.preserveThinFeatures ?? options.preserve_thin_features ?? true;
    this.thinFeatureThreshold = options.thinFeatureThreshold ?? options.thin_feature_threshold ?? 0.125;
    this.preserveOutline = options.preserveOutline ?? options.preserve_outline ?? true;
    this.preserveInternalEdges = options.preserveInternalEdges ?? options.preserve_internal_edges ?? true;
    this.outlineMinCoverage = options.outlineMinCoverage ?? options.outline_min_coverage ?? 0.02;
    this.internalEdgeThreshold = options.internalEdgeThreshold ?? options.internal_edge_threshold ?? 0.10;
    this.internalEdgeWeight = options.internalEdgeWeight ?? options.internal_edge_weight ?? 0.65;
    this.binaryAlpha = options.binaryAlpha ?? options.binary_alpha ?? null;
    this.validate();
  }

  validate() {
    for (const name of [
      'alphaThreshold',
      'sourceAlphaThreshold',
      'thinFeatureThreshold',
      'outlineMinCoverage',
      'internalEdgeThreshold',
    ]) {
      const value = this[name];
      if (!(value >= 0 && value <= 1)) {
        throw new RangeError(`${name} must be between 0 and 1, got ${value}`);
      }
    }
    if (this.internalEdgeWeight < 0) {
      throw new RangeError('internalEdgeWeight must be non-negative');
    }
    if (this.binaryAlpha !== null && typeof this.binaryAlpha !== 'boolean') {
      throw new TypeError('binaryAlpha must be true, false, or null');
    }
    return this;
  }
}

export function normalizeOptions(options) {
  return options instanceof DownscaleOptions ? options : new DownscaleOptions(options ?? {});
}
