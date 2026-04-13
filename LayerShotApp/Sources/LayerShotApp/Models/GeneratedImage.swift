import Foundation

public struct GeneratedImage: Identifiable {
    public var id = UUID()
    public var url: URL
    public var productName: String
    public var color: String
    public var view: String
    public var variant: Int
    public var qualityScore: Double?
    public var recommendation: String?

    public var filename: String { url.lastPathComponent }

    public init(url: URL, productName: String, color: String, view: String, variant: Int, qualityScore: Double? = nil, recommendation: String? = nil) {
        self.url = url
        self.productName = productName
        self.color = color
        self.view = view
        self.variant = variant
        self.qualityScore = qualityScore
        self.recommendation = recommendation
    }

    /// Parse from filename convention: `product_color_view_variant.png`
    public static func from(url: URL) -> GeneratedImage? {
        let name  = url.deletingPathExtension().lastPathComponent
        let parts = name.split(separator: "_")
        guard parts.count >= 4, let variant = Int(parts[3]) else { return nil }
        return GeneratedImage(
            url: url,
            productName: String(parts[0]),
            color:       String(parts[1]),
            view:        String(parts[2]),
            variant:     variant
        )
    }
}
