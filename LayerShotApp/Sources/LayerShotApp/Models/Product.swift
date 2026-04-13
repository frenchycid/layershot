import Foundation

public struct Product: Identifiable, Codable, Hashable {
    public var id = UUID()
    public var name: String
    public var color: String

    public var cliArgument: String { "\(name):\(color)" }

    public init(name: String, color: String) {
        self.name = name
        self.color = color
    }
}
