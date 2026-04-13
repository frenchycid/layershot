import Foundation

public struct StyleAnalysis: Codable {
    public var lighting: String
    public var colorPalette: [String]
    public var grain: String
    public var lens: String
    public var atmosphere: String
    public var styleSummary: String

    public init(lighting: String, colorPalette: [String], grain: String, lens: String, atmosphere: String, styleSummary: String) {
        self.lighting = lighting
        self.colorPalette = colorPalette
        self.grain = grain
        self.lens = lens
        self.atmosphere = atmosphere
        self.styleSummary = styleSummary
    }

    enum CodingKeys: String, CodingKey {
        case lighting, grain, lens, atmosphere
        case colorPalette = "color_palette"
        case styleSummary = "style_summary"
    }
}
