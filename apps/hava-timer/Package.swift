// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "hava-timer",
    platforms: [.macOS(.v13)],
    products: [.executable(name: "hava-timer", targets: ["HavaTimer"])],
    targets: [.executableTarget(name: "HavaTimer", resources: [.process("Resources")])]
)
