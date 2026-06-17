// Bảo vệ React khỏi crash khi trình duyệt tự dịch trang (Google Translate / extension dịch).
//
// Cơ chế lỗi: trình dịch thay text-node của React bằng <font> wrapper. Khi React render lại,
// nó gọi insertBefore/removeChild trên node đã bị dời đi → "NotFoundError: Failed to execute
// 'insertBefore' on 'Node': The node ... is not a child of this node" và cây UI vỡ.
//
// Fix kinh điển: bọc 2 hàm DOM này — nếu node tham chiếu không còn là con của parent thì
// no-op an toàn thay vì ném lỗi. <meta notranslate> ngăn Chrome built-in, patch này phủ thêm
// các extension dịch (vốn bỏ qua meta). Chỉ chạy 1 lần khi app khởi động.
export function installDomTranslateGuard(): void {
  if (typeof Node !== "function" || !Node.prototype) return;

  const originalInsertBefore = Node.prototype.insertBefore;
  Node.prototype.insertBefore = function <T extends Node>(newNode: T, referenceNode: Node | null): T {
    if (referenceNode && referenceNode.parentNode !== this) return newNode;
    return originalInsertBefore.call(this, newNode, referenceNode) as T;
  };

  const originalRemoveChild = Node.prototype.removeChild;
  Node.prototype.removeChild = function <T extends Node>(child: T): T {
    if (child.parentNode !== this) return child;
    return originalRemoveChild.call(this, child) as T;
  };
}
