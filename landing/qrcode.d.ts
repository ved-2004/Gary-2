declare module "qrcode" {
  interface QRCodeModules {
    size: number;
    get(x: number, y: number): boolean;
  }

  interface QRCodeModel {
    modules: QRCodeModules;
  }

  interface QRCodeCreateOptions {
    errorCorrectionLevel?: "L" | "M" | "Q" | "H";
    margin?: number;
  }

  const QRCode: {
    create(text: string, options?: QRCodeCreateOptions): QRCodeModel;
  };

  export default QRCode;
}
