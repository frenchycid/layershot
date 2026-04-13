import Foundation

public struct MasterPrompt: Codable {
    public var basePrompt: String
    public var viewVariants: [String: String]
    public var negativePrompt: String

    public init(basePrompt: String, viewVariants: [String: String], negativePrompt: String) {
        self.basePrompt = basePrompt
        self.viewVariants = viewVariants
        self.negativePrompt = negativePrompt
    }

    enum CodingKeys: String, CodingKey {
        case basePrompt    = "base_prompt"
        case viewVariants  = "view_variants"
        case negativePrompt = "negative_prompt"
    }
}
